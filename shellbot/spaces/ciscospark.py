# -*- coding: utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bottle import request
from functools import wraps
import itertools
import logging
from multiprocessing import Process, Queue
import os
import re
import requests
from six import string_types
import tempfile
import time

from shellbot.channel import Channel
from shellbot.events import Event, Message, Join, Leave
from .base import Space


def retry(give_up="Unable to request Cisco Spark API",
          silent=False,
          delays=(0.1, 1, 5),
          skipped=(401, 403, 404, 409)):
    """
    Improves a call to Cisco Spark API

    :param give_up: message to log on final failure
    :type give_up: str

    :param silent: if exceptions should be masked as much as possible
    :type silent: bool

    :param delays: time to wait between repetitions
    :type delays: a list of positive numbers

    :param skipped: do not retry for these status codes
    :type skipped: a list of web status codes

    This decorator compensates for common transient communication issues
    with the Cisco Spark platform in the cloud.

    Example::

        @retry(give_up="Unable to get information on this bot")
        def api_call():
            return self.api.people.me()

        me = api_call()

    credit: http://code.activestate.com/recipes/580745-retry-decorator-in-python/
    """
    def wrapper(function):
        def wrapped(*args, **kwargs):

            from ciscosparkapi import SparkApiError

            for delay in itertools.chain(delays, [ None ]):

                try:
                    return function(*args, **kwargs)

                except Exception as feedback:
                    if isinstance(feedback, SparkApiError) and feedback.response_code in skipped:
                        delay = None

                    if str(feedback).startswith("TEST"):  # horrible hack, right?
                        delay = None

                    if delay is None:
                        logging.warning(give_up)

                        if silent:
                            logging.debug(feedback)
                            return

                        else:
                            raise

                    else:
                        logging.debug(feedback)
                        logging.warning(u"Retrying the API request...")
                        time.sleep(delay)

        return wrapped
    return wrapper


def no_exception(function, return_value=None):
    """
    Stops the propagation of exceptions

    :param return_value: Returned by the decorated function on exception

    This decorator is a convenient approach for silently discarding
    exceptions.

    #wip -- this should be moved in a general-purpose module of shellbot

    Example::

        @no_exception(return_value=[])
        def list_items():
            ...  # if an exception is raised here, an empty list is returned

    """
    def wrapper(*args, **kwargs):

        wraps(function)
        try:
            return function(*args, **kwargs)

        except Exception as feedback:
            logging.debug(feedback)
            return return_value

    return wrapper


class SparkSpace(Space):
    """
    Handles a Cisco Spark room

    This is a representation of a chat space hosted at Cisco Spark.

    """

    DEFAULT_SETTINGS = {

        'spark': {
            'room': '$CHAT_ROOM_TITLE',
        },

        'server': {
            'url': '$SERVER_URL',
            'hook': '/hook',
            'binding': '0.0.0.0',
            'port': 8080,
        },

    }

    def on_init(self,
                prefix='spark',
                token=None,
                **kwargs):
        """
        Handles extended initialisation parameters

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        :param token: bot authentication token for the Cisco Spark API
        :type token: str

        Example::

            space = SparkSpace(context=context, prefix='spark.audit')

        Here we create a new space powered by Cisco Spark service, and use
        settings under the key ``spark`` in the context of this bot.
        """
        assert prefix not in (None, '')
        self.prefix = prefix

        if token not in (None, ''):
            self.set('token', token)

        self.api = None
        self.audit_api = None

        self._last_message_id = 0

    def check(self):
        """
        Checks settings of the space

        This function reads key ``spark`` and below, and update
        the context accordingly::

           space.configure({'spark': {
               'room': 'My preferred room',
               'participants':
                  ['alan.droit@azerty.org', 'bob.nard@support.tv'],
               'team': 'Anchor team',
               'token': '$MY_BOT_TOKEN',
               }})

        This can also be written in a more compact form::

           space.configure({'spark.room': 'My preferred room',
               'spark.token': '$MY_BOT_TOKEN',
               })

        This function handles following parameters:

        * ``spark.room`` - title of the associated Cisco Spark room.
          This can refer to an environment variable if it starts
          with ``$``, e.g., ``$ROOM_TITLE``.

        * ``spark.participants`` - list of initial participants. This can
          be taken from ``$CHANNEL_DEFAULT_PARTICIPANTS`` from the
          environment.

        * ``spark.team`` - title of a team associated with this room

        * ``spark.token`` - private token of the bot, given by Cisco Spark.
          Instead of putting the real value of the token you are encouraged
          to use an environment variable instead,
          e.g., ``$MY_BOT_TOKEN``.
          If ``spark.token`` is not provided, then the function looks for an
          environment variable ``CISCO_SPARK_BOT_TOKEN``.

        * ``spark.audit_token`` - token to be used for the audit of chat events.
          It is recommended that a token of a person is used, so that the
          visibility is maximised for the proper audit of events.
          Instead of putting the real value of the token you are encouraged
          to use an environment variable instead,
          e.g., ``$MY_AUDIT_TOKEN``.
          If ``spark.audit_token`` is not provided, then the function looks
          for an environment variable ``CISCO_SPARK_AUDIT_TOKEN``.

        If a single value is provided for ``participants`` then it is turned
        automatically to a list.

        Example::

            >>>space.configure({'spark.participants': 'bobby@jah.com'})
            >>>space.context.get('spark.participants')
            ['bobby@jah.com']

        """
        self.context.check(self.prefix+'.room',
                           is_mandatory=True, filter=True)
        self.context.check(self.prefix+'.participants',
                           '$CHANNEL_DEFAULT_PARTICIPANTS', filter=True)
        self.context.check(self.prefix+'.team')
        self.context.check(self.prefix+'.token',
                           '$CISCO_SPARK_BOT_TOKEN', filter=True)

        self.context.check(self.prefix+'.audit_token',
                           '$CISCO_SPARK_AUDIT_TOKEN', filter=True)

        values = self.context.get(self.prefix+'.participants')
        if isinstance(values, string_types):
            self.context.set(self.prefix+'.participants', [values])

    def configured_title(self):
        """
        Returns the title of the space as set in configuration

        :return: the configured title, or ``Collaboration space``
        :rtype: str

        This function should be rewritten in sub-classes if
        space title does not come from ``space.room`` parameter.
        """
        return self.get('room', self.DEFAULT_SPACE_TITLE)

    def connect(self, factory=None, **kwargs):
        """
        Connects to the back-end API

        :parameter factory: an API factory, for test purpose
        :type: object

        If a factory is provided, it is used to get API instances. Else
        the regular CiscoSparkAPI is invoked instead.

        This function loads two instances of Cisco Spark API, one using
        the bot token, and one using the audit token, if this is available.
        """
        if not factory:
            from ciscosparkapi import CiscoSparkAPI
            factory = CiscoSparkAPI

        logging.debug(u"Loading Cisco Spark API")

        bot_token = self.get('token')
        assert bot_token not in (None, '')  # some token is needed

        self.api = None
        try:
            logging.debug(u"- token: {}".format(bot_token))
            self.api = factory(access_token=bot_token)

        except Exception as feedback:
            logging.error(u"Unable to load Cisco Spark API")
            logging.exception(feedback)

        audit_token = self.get('audit_token')
        self.audit_api = None
        if audit_token:
            try:
                logging.debug(u"- audit token: {}".format(audit_token))
                self.audit_api = factory(access_token=audit_token)

            except Exception as feedback:
                logging.warning(feedback)

        self.on_connect()

    def on_connect(self):
        """
        Retrieves attributes of this bot

        This function queries the Cisco Spark API to remember the id of this
        bot. This is used afterwards to filter inbound messages to the shell.

        """
        assert self.api is not None  # connect() is prerequisite

        @retry(u"Unable to retrieve bot information")
        def bot_identity():
            return self.api.people.me()

        logging.debug(u"Retrieving bot information")
        me = bot_identity()
#       logging.debug(u"- {}".format(str(me)))

        self.context.set('bot.address', str(me.emails[0]))
        logging.debug(u"- bot email: {}".format(
            self.context.get('bot.address')))

        self.context.set('bot.name',
                     str(me.displayName))
        logging.debug(u"- bot name: {}".format(
            self.context.get('bot.name')))

        self.context.set('bot.id', me.id)
        logging.debug(u"- bot id: {}".format(
            self.context.get('bot.id')))

    def list_group_channels(self, quantity=10, **kwargs):
        """
        Lists available channels

        :param quantity: maximum quantity of channels to return
        :type quantity: positive integer

        :return: list of Channel

        """
        assert quantity >= 0

        if not quantity:
            return []

        logging.info(u"Listing {} recent rooms".format(quantity))

        @retry(u"Unable to list rooms", silent=True)
        def list_rooms():
            return [self._to_channel(x) \
                        for x in self.api.rooms.list(type='group',
                                                     sortBy='lastactivity',
                                                     max=quantity)]

        return list_rooms()[:quantity]  # enforce the maximum results

    def create(self, title, ex_team=None, **kwargs):
        """
        Creates a room

        :param title: title of a new channel
        :type title: str

        :param ex_team: the team attached to this room (optional)
        :type ex_team: str or object

        If the parameter ``ex_team`` is provided, then it can be either a
        simple name, or a team object featuring an id.

        :return: Channel or None

        This function returns a representation of the local channel.

        """
        assert title not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        teamId = None
        if ex_team:
            try:
                teamId = ex_team.id
            except:
                team = self.get_team(ex_team)
                if team and team.id:
                    teamId = team.id

        logging.info(u"Creating Cisco Spark room '{}'".format(title))

        @retry(u"Unable to create room", silent=True)
        def do_it():

            room = self.api.rooms.create(title=title,
                                         teamId=teamId)

            return self._to_channel(room)

        return do_it()

    def get_by_title(self, title, **kwargs):
        """
        Looks for an existing room by name

        :param title: title of the target room
        :type title: str

        :return: Channel instance or None

        Note: This function looks only into group rooms. To get a direct room
        use ``get_by_person()`` instead.
        """
        assert title not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        logging.info(u"Looking for Cisco Spark room '{}'".format(title))

        @retry(u"Unable to list rooms", silent=True)
        def do_it():

            for room in self.api.rooms.list(type='group'):

                if title == room.title:
                    logging.info(u"- found it")
                    return self._to_channel(room)

            logging.info(u"- not found")

        return do_it()

    def get_by_id(self, id, **kwargs):
        """
        Looks for an existing room by id

        :param id: identifier of the target room
        :type id: str

        :return: Channel instance or None

        """
        assert id not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        logging.info(u"Using Cisco Spark room '{}'".format(id))

        @retry(u"Unable to list rooms", silent=True)
        def do_it():

            room = self.api.rooms.get(id)
            if room:
                logging.info(u"- found it")
                return self._to_channel(room)

            logging.info(u"- not found")

        return do_it()

    def get_by_person(self, label, **kwargs):
        """
        Looks for an existing private room with a person

        :param label: the display name of the person's account
        :type label: str

        :return: Channel instance or None

        If a channel already exists for this person, a representation of it is
        returned. Else the value ``None``is returned.

        """
        assert label not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        logging.info(
            u"Looking for Cisco Spark private room with '{}'".format(label))

        @retry(u"Unable to list rooms", silent=True)
        def do_it():

            for room in self.api.rooms.list(type='direct'):

                if room.title.startswith(label):
                    logging.info(u"- found it")
                    return self._to_channel(room)

            logging.info(u"- not found")

        return do_it()

    def update(self, channel, **kwargs):
        """
        Updates an existing room

        :param channel: a representation of the updated room
        :type channel: Channel

        This function can change the title of a room.

        For example, change the title from a bot instance::

            bot.channel.title = "A new title"
            bot.space.update(bot.channel)

        """
        assert channel is not None
        assert self.api is not None  # connect() is prerequisite

        @retry(u"Unable to update room", silent=True)
        def do_it():
            self.api.rooms.update(channel.id, channel.title)

        do_it()

    def delete(self, id, **kwargs):
        """
        Deletes a room

        :param id: the unique id of an existing room
        :type id: str

        """
        assert id not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        logging.info(u"Deleting Cisco Spark room '{}'".format(id))

        @retry(u"Unable to delete room", silent=True)
        def do_it():
            self.api.rooms.delete(roomId=id)

        do_it()

    def get_team(self, name):
        """
        Gets a team by name

        :param name: name of the target team
        :type name: str

        :return: attributes of the team
        :rtype: Team or None

        >>>print(space.get_team("Hello World"))
        Team({
          "id" : "Y2lzY29zcGFyazovL3VzL1RFQU0Yy0xMWU2LWE5ZDgtMjExYTBkYzc5NzY5",
          "name" : "Hello World",
          "created" : "2015-10-18T14:26:16+00:00"
        })

        """
        assert name not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        logging.info(u"Looking for Cisco Spark team '{}'".format(name))

        @retry(u"Unable to list teams", silent=True)
        def do_it():

            for team in self.api.teams.list():

                if name == team.name:
                    logging.info(u"- found team")
                    return team

            logging.info(u"- team not found")

        return do_it()

    def list_participants(self, id):
        """
        Lists participants to a channel

        :param id: the unique id of an existing channel
        :type id: str

        :return: a list of persons
        :rtype: list of str

        Note: this function returns all participants, except the bot itself.
        """
        assert id not in (None, '')  # target channel is required

        logging.debug(
            u"Looking for Cisco Spark room participants")

        @retry(u"Unable to list memberships", silent=True)
        def do_it():

            participants = set()

            avoided = set()
            avoided.add(self.context.get('bot.address'))
            for item in self.api.memberships.list(roomId=id):

                person = item.personEmail
                if person in avoided:
                    continue

                logging.debug(u"- {}".format(item.personEmail))
                participants.add(person)

            return participants

        return do_it()

    @no_exception
    def add_participant(self, id, person, is_moderator=False):
        """
        Adds one participant

        :param id: the unique id of an existing room
        :type id: str

        :param person: e-mail address of the person to add
        :type person: str

        :param is_moderator: if this person has special powers on this channel
        :type is_moderator: True or False

        """
        assert id not in (None, '')  # target channel is required
        assert person not in (None, '')
        assert is_moderator in (True, False)
        assert self.api is not None  # connect() is prerequisite

        @retry(u"Unable to add participant '{}'".format(person), silent=True)
        def do_it():
            self.api.memberships.create(roomId=id,
                                        personEmail=person,
                                        isModerator=is_moderator)

        do_it()

    @no_exception
    def remove_participant(self, id, person):
        """
        Removes a participant

        :param id: the unique id of an existing room
        :type id: str

        :param person: e-mail address of the person to remove
        :type person: str

        """
        assert id not in (None, '')  # target channel is required
        assert person not in (None, '')  # target person
        assert self.api is not None  # connect() is prerequisite

        @retry(u"Unable to remove participant '{}'".format(person), silent=True)
        def do_it():
            self.api.memberships.delete(roomId=id,
                                        personEmail=person)

        do_it()

    def walk_messages(self,
                      id=None,
                      **kwargs):
        """
        Walk messages from a Cisco Spark room

        :param id: the unique id of an existing room
        :type id: str

        :return: an iterator of Message objects

        """
        assert self.api is not None  # connect() is prerequisite

        for item in self.api.messages.list(roomId=id):
            item._json['hook'] = 'shellbot-messages'
            yield self.on_message(item._json)

    def post_message(self,
                     id=None,
                     text=None,
                     content=None,
                     file=None,
                     person=None,
                     **kwargs):
        """
        Posts a message to a Cisco Spark room

        :param id: the unique id of an existing room
        :type id: str

        :param person: address for a direct message
        :type person: str

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as Markdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        Example message out of plain text::

           space.post_message(id=id, text='hello world')

        Example message with Markdown::

           space.post_message(id, content='this is a **bold** statement')

        Example file upload::

           space.post_message(id, file='./my_file.pdf')

        Of course, you can combine text with the upload of a file::

           text = 'This is the presentation that was used for our meeting'
           space.post_message(id=id,
                              text=text,
                              file='./my_file.pdf')

        For direct messages, provide who you want to reach instead of
        a channel id, like this::

            space.post_message(person='foo.bar@acme.com', text='hello guy')

        """
        assert id or person  # need a recipient
        assert id is None or person is None  # only one recipient
        assert self.api is not None  # connect() is prerequisite

        logging.info(u"Posting message")
        if text not in (None, ''):
            logging.debug(u"- text: {}".format(
                text[:50] + (text[50:] and '..')))
        if content not in (None, ''):
            logging.debug(u"- content: {}".format(
                content[:50] + (content[50:] and '..')))
        if file not in (None, ''):
            logging.debug(u"- file: {}".format(
                file[:50] + (file[50:] and '..')))

        @retry(u"Unable to post message", silent=True)
        def do_it():
            files = [file] if file else None
            self.api.messages.create(roomId=id,
                                     toPersonEmail=person,
                                     text=text,
                                     markdown=content,
                                     files=files)

        do_it()

    def register(self, hook_url):
        """
        Connects in the background to Cisco Spark inbound events

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        This function registers the provided hook multiple times, so as to
        receive mutiple kind of updates:

        - The bot is invited to a room, or kicked out of it. People are
          joining or leaving:
          webhook name = shellbot-memberships
          resource = memberships,
          event = all,
          registered with bot token

        - Messages are sent, maybe with some files:
          webhook name = shellbot-messages
          resource = messages,
          event = created,
          registered with bot token

        - Messages sent, maybe with some files, for audit purpose:
          webhook name = shellbot-audit
          resource = messages,
          event = created,
          registered with audit token

        Previous webhooks registered with the bot token are all removed before
        registration. This means that only the most recent instance of the bot
        will be notified of new invitations.

        """
        assert hook_url not in (None, '')
        assert self.api is not None  # connect() is prerequisite

        self.deregister()

        @retry(u"Unable to create webhook", silent=True)
        def create_webhook(api, name, resource, event, filter):
            api.webhooks.create(name=name,
                                targetUrl=hook_url,
                                resource=resource,
                                event=event,
                                filter=filter)

        logging.info(u"Registering webhook to Cisco Spark")
        logging.debug(u"- url: {}".format(hook_url))

        logging.debug(u"- registering 'shellbot-memberships'")
        create_webhook(api=self.api,
                       name='shellbot-memberships',
                       resource='memberships',
                       event='all',
                       filter=None)

        logging.debug(u"- registering 'shellbot-messages'")
        create_webhook(api=self.api,
                       name='shellbot-messages',
                       resource='messages',
                       event='created',
                       filter=None)

        if self.audit_api and self.fan:
            self.context.set('audit.has_been_armed', True)
            logging.debug(u"- registering 'shellbot-audit'")
            create_webhook(api=self.audit_api,
                           name='shellbot-audit',
                           resource='messages',
                           event='created',
                           filter=None)

    def deregister(self):
        """
        Stops inbound flow from Cisco Spark

        This function deregisters hooks that it may have created.

        Previous webhooks registered with the bot token are all removed before
        registration. This means that only the most recent instance of the bot
        will be notified of new invitations.

        This function also removes webhooks created with the audit token, if
        any. So after deregister the audit of individual rooms just stops.

        """
        assert self.api is not None  # connect() is prerequisite

        @retry(u"Unable to list webhooks", silent=True)
        def list_webhooks(api):
            return [x for x in api.webhooks.list()]

        @retry(u"Unable to delete webhook", silent=True)
        def delete_webhook(api, id):
            api.webhooks.delete(webhookId=id)

        logging.info(u"Purging webhooks")
        for webhook in list_webhooks(self.api):
            logging.debug(u"- deleting '{}'".format(webhook.name))
            delete_webhook(self.api, webhook.id)

        if self.audit_api:
            for webhook in list_webhooks(self.audit_api):
                logging.debug(u"- deleting '{}'".format(webhook.name))
                delete_webhook(self.audit_api, webhook.id)

    def webhook(self, item=None):
        """
        Processes the flow of events from Cisco Spark

        :param item: if provided, do not invoke the ``request`` object
        :type item: dict

        This function is called from far far away, over the Internet,
        most of the time. Or it is called locally, from test environment,
        when an item is provided.

        The structure of the provided item should be identical to those of
        updates sent by Cisco Spark.

        Example event on message creation::

            {
                "resource": "messages",
                "event": "created",
                "data": { "id": "...." },
                "name": "shellbot-audit"
            }

        """

        logging.debug(u'Receiving data from webhook')

        if not item:
            item = request.json
        assert isinstance(item, dict)

#        logging.debug(u"- {}".format(item))
        resource = item['resource']
        event = item['event']
        data = item['data']
        hook = item['name']

        if hook == 'shellbot-audit':
            logging.debug(u"- for audit")
            api = self.audit_api
            queue = self.fan

        else:
            api = self.api
            queue = self.ears

        if resource == 'messages' and event == 'created':

            if hook != 'shellbot-audit':

                filter_id = self.context.get('bot.id')
                if filter_id and data.get('personId') == filter_id:
                    logging.debug(u"- sent by me, thrown away")
                    return 'OK'

            logging.debug(u"- handling '{}:{}'".format(resource, event))

            @retry(u"Unable to retrieve new message")
            def fetch_message():

                item = api.messages.get(messageId=data['id'])
                item._json['hook'] = hook
                return item._json

            self.on_message(fetch_message(), queue)

        elif resource == 'memberships' and event == 'created':
            logging.debug(u"- handling '{}:{}'".format(resource, event))
            self.on_join(data, queue)

        elif resource == 'memberships' and event == 'deleted':
            logging.debug(u"- handling '{}:{}'".format(resource, event))
            self.on_leave(data, queue)

        else:
            logging.debug(u"- throwing away {}:{}".format(resource, event))
            logging.debug(u"- {}".format(data))

        return "OK"

    def pull(self):
        """
        Fetches events from Cisco Spark

        This function senses most recent items, and pushes them
        to a processing queue.
        """
        assert self.api is not None  # connect() is prerequisite

        logging.info(u'Pulling messages')
        self.context.increment(u'puller.counter')

        @retry(u"Unable to pull messages", silent=True)
        def call_api():
            return self.api.messages.list(mentionedPeople=['me'],
                                          max=10)

        new_items = []
        items = call_api()
        for item in items:

            if item.id == self._last_message_id:
                break

            new_items.append(item)

        if len(new_items):
            logging.info(u"Pulling {} new messages".format(len(new_items)))

        while len(new_items):
            item = new_items.pop()
            self._last_message_id = item.id
            item._json['hook'] = 'pull'
            self.on_message(item._json, self.ears)

    def on_message(self, item, queue=None):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue (optional)
        :type queue: Queue

        :return: a Message

        This function prepares a Message and push it to the provided queue.

        This function adds following keys to messages so that a neutral format
        can be used with the listener:

        * ``type`` is set to ``message``
        * ``content`` is a copy of ``html``
        * ``from_id`` is a copy of ``personId``
        * ``from_label`` is a copy of ``personEmail``
        * ``is_direct`` if the message is coming from 1:1 room
        * ``mentioned_ids`` is a copy of ``mentionedPeople``
        * ``channel_id`` is a copy of ``roomId``
        * ``stamp`` is a copy of ``created``

        """
        message = Message(item.copy())
        message.content = message.get('html', message.text)
        message.from_id = message.get('personId')
        message.from_label = message.get('personEmail')
        message.is_direct = True if message.get('roomType') == 'direct' else False
        message.mentioned_ids = message.get('mentionedPeople', [])
        message.channel_id = message.get('roomId')
        message.stamp = message.get('created')

        files = item.get('files', [])
        if files:
            url = files[0]
            message.url = url

            if message.hook == 'shellbot-audit':
                token = self.get('audit_token', '*no*token')
            else:
                token = self.get('token', '*no*token')

            message.attachment = self.name_attachment(url, token=token)

        if queue:
            logging.debug(u"- putting message to queue")
            queue.put(str(message))

        return message

    def download_attachment(self, url, token=None):
        """
        Copies a shared document locally
        """
        path = tempfile.gettempdir()+'/'+self.name_attachment(url, token=token)
        logging.debug(u"- writing to {}".format(path))
        with open(path, "w+b") as handle:
            handle.write(self.get_attachment(url, token=token))

        return path

    def name_attachment(self, url, token=None, response=None):
        """
        Retrieves a document attached to a room
        """
        logging.debug(u"- sensing {}".format(url))

        if not token:
            token = self.get('token', '*no*token')

        headers = {}
        headers['Authorization'] = 'Bearer '+token

        if not response:
            response = requests.head(url=url, headers=headers)

#        logging.debug(u"- status: {}".format(response.status_code))
        if response.status_code != 200:
            raise Exception(u"Unable to download attachment")

#        logging.debug(u"- headers: {}".format(response.headers))
        line = response.headers['Content-Disposition']
        match = re.search('filename=(.+)', line)
        if match:
            name = match.group(1).strip()
            if name.startswith('"') and name.endswith('"'):
                name = name[1:-1]
            return name

        return 'downloadable'

    def get_attachment(self, url, token=None, response=None):
        """
        Retrieves a document attached to a room
        """
        logging.debug(u"- fetching {}".format(url))

        if not token:
            token = self.get('token', '*no*token')

        headers = {}
        headers['Authorization'] = 'Bearer '+token

        if not response:
            response = requests.get(url=url, headers=headers)

#        logging.debug(u"- status: {}".format(response.status_code))
        if response.status_code != 200:
            raise Exception(u"Unable to download attachment")

#        logging.debug(u"- headers: {}".format(response.headers))
#        logging.debug(u"- encoding: {}".format(response.encoding))
        logging.debug(u"- length: {}".format(len(response.content)))
        return response.content

    def on_join(self, item, queue=None):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue (optional)
        :type queue: Queue

        Example item received on memberships:create::

            {
                'isMonitor': False,
                'created': '2017-05-31T21:25:30.424Z',
                'personId': 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U',
                'isModerator': False,
                'personOrgId': 'Y2lzY29zcGFyazovL3V0FOSVpBVElPTi9jb25zdW1lcg',
                'personDisplayName': 'foo.bar@acme.com',
                'personEmail': 'foo.bar@acme.com',
                'roomId': 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz',
                'id': 'Y2lzY29zcGFyazovL3VzDctMTFlNy05OTAwLTA1OTAyNmIwYjQ1Mw'
            }

        This function prepares a Join and push it to the provided queue.

        * ``type`` is set to ``join``
        * ``actor_id`` is a copy of ``personId``
        * ``actor_address`` is a copy of ``personEmail``
        * ``actor_label`` is a copy of ``personDisplayName``
        * ``stamp`` is a copy of ``created``

        """
        join = Join(item.copy())
        join.actor_id = join.get('personId')
        join.actor_address = join.get('personEmail')
        join.actor_label = join.get('personDisplayName')
        join.channel_id = join.get('roomId')
        join.stamp = join.get('created')

        if queue:
            logging.debug(u"- putting join to queue")
            queue.put(str(join))

        return join

    def on_leave(self, item, queue=None):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue (optional)
        :type queue: Queue

        Example item received on memberships:delete::

            {
                'isMonitor': False,
                'created': '2017-05-31T21:25:30.424Z',
                'personId': 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U',
                'isModerator': False,
                'personOrgId': 'Y2lzY29zcGFyazovL3V0FOSVpBVElPTi9jb25zdW1lcg',
                'personDisplayName': 'foo.bar@acme.com',
                'personEmail': 'foo.bar@acme.com',
                'roomId': 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz',
                'id': 'Y2lzY29zcGFyazovL3VzDctMTFlNy05OTAwLTA1OTAyNmIwYjQ1Mw'
            }

        This function prepares a Leave and push it to the provided queue.

        * ``type`` is set to ``leave``
        * ``actor_id`` is a copy of ``personId``
        * ``actor_address`` is a copy of ``personEmail``
        * ``actor_label`` is a copy of ``personDisplayName``
        * ``stamp`` is a copy of ``created``

        """
        leave = Leave(item.copy())
        leave.actor_id = leave.get('personId')
        leave.actor_address = leave.get('personEmail')
        leave.actor_label = leave.get('personDisplayName')
        leave.channel_id = leave.get('roomId')
        leave.stamp = leave.get('created')

        if queue:
            logging.debug(u"- putting leave to queue")
            queue.put(str(leave))

        return leave

    def _to_channel(self, room):
        """
        Turns a Cisco Spark room to a shellbot channel

        :param room: the representation to use

        :return: Channel
        """
        channel = Channel()
        channel.title = room.title
        channel.id = room.id
        channel.type = room.type
        channel.is_group = True if room.type in ("group", "team") else False
        channel.is_team = True if room.type == "team" else False
        channel.is_direct = True if room.type == "direct" else False
        channel.is_moderated = True if room.isLocked else False

        try:
            channel.team_id = room.teamId
        except:
            channel.team_id = None

        return channel
