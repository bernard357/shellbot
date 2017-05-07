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
import logging
from multiprocessing import Process, Queue
import os
from six import string_types
import time

from ..context import Context
from .base import Space


class SparkSpace(Space):
    """
    Handles a Cisco Spark room
    """

    def on_init(self,
                prefix='spark',
                token=None,
                **kwargs):
        """
        Handles extended initialisation parameters

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        :param token: authentication token for the Cisco Spark API

        Example::

            space = SparkSpace(bot=bot, prefix='spark.audit')

        Here we create a new space powered by Cisco Spark service, and use
        settings under the key ``spark.audit`` in the context of this bot.
        """
        assert prefix not in (None, '')
        self.prefix = prefix

        if token is not None:
            self.bot.context.set(self.prefix+'.token', token)

        self.api = None

    def on_reset(self):
        """
        Resets extended internal variables
        """
        self.teamId = None

        self.token = self.bot.context.get(self.prefix+'.token', '*void')
        self.personal_token = self.bot.context.get(self.prefix+'.personal_token', '*void')

        self._last_message_id = 0

    def check(self):
        """
        Checks settings of the space

        This function reads key ``spark`` and below, and update
        the context accordingly.

        >>>space.configure({'spark': {
               'room': 'My preferred room',
               'moderators':
                  ['foo.bar@acme.com', 'joe.bar@corporation.com'],
               'participants':
                  ['alan.droit@azerty.org', 'bob.nard@support.tv'],
               'team': 'Anchor team',
               'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
               'personal_token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
               }})

        This can also be written in a more compact form::

        >>>space.configure({'spark.room': 'My preferred room',
               'spark.token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
               })

        This function handles following parameters:

        * ``spark.room`` - title of the associated Cisco Spark room

        * ``spark.moderators`` - list of persons assigned as room moderators

        * ``spark.participants`` - list of initial participants

        * ``spark.team`` - title of a team associated with this room

        * ``spark.token`` - private token of the bot, given by Cisco Spark.
          If ``spark.token`` is not provided, then the function looks for an
          environment variable ``CISCO_SPARK_BOT_TOKEN`` instead.

        * ``spark.personal_token`` - private token of a human being
          If ``spark.personal_token`` is not provided, then the function looks
          for an environment variable ``CISCO_SPARK_TOKEN`` instead.

        If a single value is provided for ``moderators`` or for
        ``participants`` then it is turned automatically to a list.

        >>>space.configure({'spark.moderators': 'bobby@jah.com'})
        >>>space.context.get('spark.moderators')
        ['bobby@jah.com']

        """
        if self.bot.context.get(self.prefix+'.personal_token') is None:
            token = os.environ.get('CISCO_SPARK_TOKEN')
            if token:
                self.bot.context.set(self.prefix+'.personal_token', token)

        if self.bot.context.get(self.prefix+'.token') is None:
            token1 = os.environ.get('CISCO_SPARK_BOT_TOKEN')
            token2 = self.bot.context.get(self.prefix+'.personal_token')
            if token1:
                self.bot.context.set(self.prefix+'.token', token1)
            elif token2:
                self.bot.context.set(self.prefix+'.token', token2)

        self.bot.context.check(self.prefix+'.room', filter=True)
        self.bot.context.check(self.prefix+'.moderators', [], filter=True)
        self.bot.context.check(self.prefix+'.participants', [])
        self.bot.context.check(self.prefix+'.team')
        self.bot.context.check(self.prefix+'.token', '', filter=True)
        self.bot.context.check(self.prefix+'.personal_token', '', filter=True)

        values = self.bot.context.get(self.prefix+'.moderators')
        if isinstance(values, string_types):
            self.bot.context.set(self.prefix+'.moderators', [values])

        values = self.bot.context.get(self.prefix+'.participants')
        if isinstance(values, string_types):
            self.bot.context.set(self.prefix+'.participants', [values])

    def configured_title(self):
        """
        Returns the title of the space as set in configuration

        :return: the configured title, or ``Collaboration space``
        :rtype: str

        For Cisco Spark configurations, this is coming
        from ``spark.room`` parameter.
        """
        return  self.bot.context.get(self.prefix+'.room',
                                     self.DEFAULT_SPACE_TITLE)

    def connect(self, **kwargs):
        """
        Connects to the back-end API
        """
        from ciscosparkapi import CiscoSparkAPI

        try:
            if self.token is None:
                self.api = None
                logging.error(u"No token to load Cisco Spark API")

            else:
                self.api = CiscoSparkAPI(access_token=self.token)
                logging.debug(u"Loaded Cisco Spark API as bot")

        except Exception as feedback:
            logging.error(u"Unable to load Cisco Spark API")
            logging.exception(feedback)

        try:
            if self.personal_token is None:
                self.personal_api = None
                logging.error(u"No token to load Cisco Spark API as person")

            else:
                self.personal_api = CiscoSparkAPI(
                    access_token=self.personal_token)
                logging.debug(u"Loaded Cisco Spark API as person")

        except Exception as feedback:
            logging.error(u"Unable to load Cisco Spark API")
            logging.exception(feedback)

    def lookup_space(self, title, **kwargs):
        """
        Looks for an existing space by name

        :param title: title of the target space
        :type title: str

        :return: True on successful lookup, False otherwise

        If a space already exists with this title, the object is configured
        to use it and the function returns True.

        Else the function returns False.
        """
        assert title not in (None, '')
        logging.info(u"Looking for Cisco Spark room '{}'".format(title))

        assert self.api is not None  # connect() is prerequisite
        try:
            for room in self.api.rooms.list():
                if title == room.title:
                    logging.info(u"- found it")
                    self.use_room(room)
                    return True

            logging.info(u"- not found")

        except Exception as feedback:
            logging.error(u"Unable to list rooms")
            logging.exception(feedback)

        return False

    def create_space(self, title, ex_team=None, **kwargs):
        """
        Creates a space

        :param title: title of the target space
        :type title: str

        :param ex_team: the team attached to this room (optional)
        :type ex_team: str or object

        If the parameter ``ex_team`` is provided, then it can be either a
        simple name, or a team object featuring an id.

        On successful space creation, this object is configured
        to use it.
        """
        teamId = None
        if ex_team:
            try:
                teamId = ex_team.id
            except:
                teamId = self.get_team(ex_team).id

        logging.info(u"Creating Cisco Spark room '{}'".format(title))

        assert self.api is not None  # connect() is prerequisite
        while True:
            try:
                room = self.api.rooms.create(title=title,
                                             teamId=teamId)
                logging.info(u"- done")

                self.use_room(room)
                break

            except Exception as feedback:
                if str(feedback).startswith('Response Code [503]'):
                    logging.debug(u'- delayed by server')
                    time.sleep(3)
                    continue

                logging.warning(u"Unable to create room ")
                logging.exception(feedback)
                break

    def use_room(self, room):
        """
        Uses this room for this space

        :param room: the representation to use

        """
        logging.info(u"Bonding to room '{}'".format(room.title))

        self.id = room.id
        self.bot.context.set(self.prefix+'.id', self.id)
        logging.debug(u"- id: {}".format(self.id))

        self.title = room.title
        self.bot.context.set(self.prefix+'.title', self.title)
        logging.debug(u"- title: {}".format(self.title))

        self.teamId = room.teamId

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
        logging.info(u"Looking for Cisco Spark team '{}'".format(name))

        assert self.api is not None  # connect() is prerequisite
        for team in self.api.teams.list():
            if name == team.name:
                logging.info(u"- found it")
                return team

        logging.warning(u"- not found")
        return None

    def add_moderator(self, person):
        """
        Adds a moderator

        :param person: e-mail address of the person to add
        :type person: str

        """
        assert self.api is not None  # connect() is prerequisite
        assert self.id is not None  # bond() is prerequisite
        try:
            self.api.memberships.create(roomId=self.id,
                                        personEmail=person,
                                        isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add moderator '{}'".format(person))
            logging.exception(feedback)

    def add_participant(self, person):
        """
        Adds a participant

        :param person: e-mail address of the person to add
        :type person: str

        """
        assert self.api is not None  # connect() is prerequisite
        assert self.id is not None  # bond() is prerequisite
        try:
            self.api.memberships.create(roomId=self.id,
                                        personEmail=person,
                                        isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add participant '{}'".format(person))
            logging.exception(feedback)

    def delete_space(self, title=None, **kwargs):
        """
        Deletes a Cisco Spark room

        :param title: title of the room to be deleted (optional)
        :type title: str

        >>>space.delete_space("Obsolete Space")

        """
        if title:
            if not self.lookup_space(title=title):  # set self.id & self.title
                logging.debug(u"No room to delete")
                return

        elif self.id and self.title:
            pass

        elif self.lookup_space(title=self.configured_title()):
            pass

        else:
            logging.debug(u"No room to delete")
            return

        logging.info(u"Deleting Cisco Spark room '{}'".format(self.title))

        assert self.api is not None  # connect() is prerequisite
        try:
            self.api.rooms.delete(roomId=self.id)

        except Exception as feedback:
            logging.warning(u"Unable to delete room")
            logging.exception(feedback)

    def post_message(self,
                     text=None,
                     ex_markdown=None,
                     ex_file_path=None):
        """
        Posts a message to a Cisco Spark room

        :param text: content of the message is plain text
        :type text: str or list of str or ``None``

        :param ex_markdown: content of the message as per Markdown
        :type ex_markdown: str or list of str or ``None``

        :param ex_file_path: location of file to be uploaded or attached
        :type ex_file_path: str or ``None``

        Example message out of plain text::

        >>>space.post_message(text='hello world')

        Example message with Markdown::

        >>>space.post_message(ex_markdown='this is a **bold** statement')

        Example file upload::

        >>>space.post_message(ex_file_path='./my_file.pdf')

        Of course, you can combine text with the upload of a file::

        >>>text = 'This is the presentation that was used for our meeting'
        >>>space.post_message(text=text,
                              ex_file_path='./my_file.pdf')

        """

        logging.info(u"Posting message")

        if self.id is None:
            self.id = self.bot.context.get(self.prefix+'.id')

        logging.debug(u"- text: {}".format(text))

        assert self.api is not None  # connect() is prerequisite
        try:
            files = [ex_file_path] if ex_file_path else None
            self.api.messages.create(roomId=self.id,
                                     text=text,
                                     markdown=ex_markdown,
                                     files=files)
            logging.debug(u"- done")

        except Exception as feedback:
            logging.warning(u"Unable to post message")
            logging.exception(feedback)

    def register(self, hook_url):
        """
        Connects in the background to Cisco Spark inbound events

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        This function registers the provided hook to Cisco Spark.
        """
        assert self.is_ready  # bond() is prerequisite
        assert hook_url not in (None, '')

        logging.info(u"Registering webhook to Cisco Spark")
        logging.debug(u"- {}".format(hook_url))

        assert self.api is not None  # connect() is prerequisite
        try:
            self.api.webhooks.create(name='shellbot-webhook',
                                     targetUrl=hook_url,
                                     resource='messages',
                                     event='created',
                                     filter='roomId='+self.id)

            logging.debug(u"- done")

        except Exception as feedback:
            logging.warning(u"Unable to add webhook")
            logging.exception(feedback)

    def on_run(self):
        """
        Retrieves attributes of this bot

        This function queries the Cisco Spark API to remember the id of this
        bot. This is used afterwards to filter inbound messages to the shell.

        """
        assert self.api is not None  # connect() is prerequisite

        try:
            me = self.api.people.me()
            self.bot.context.set('bot.name',
                                 str(me.displayName.split(' ')[0]))
            logging.debug(u"Bot name: {}".format(
                self.bot.context.get('bot.name')))

            self.bot.context.set('bot.id', me.id)

        except Exception as feedback:
            logging.warning(u"Unable to retrieve bot id")
            logging.exception(feedback)

    def webhook(self, message_id=None):
        """
        Processes the flow of events from Cisco Spark

        :param message_id: if provided, do not invoke the request object

        Example message received from Cisco Spark::

            {
              "id" : "Y2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "PROJECT UPDATE - A new project plan has been published on Box: http://box.com/s/lf5vj. The PM for this project is Mike C. and the Engineering Manager is Jane W.",
              "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
              "files" : [ "http://www.example.com/images/media.png" ],
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
            }

        This function adds following keys so that a neutral format
        can be used with the listener:

        * ``type`` is set to ``message``
        * ``from_id`` is a copy of ``personId``
        * ``mentioned_ids`` is a copy of ``mentionedPeople``


        This function is called from far far away, over the Internet,
        when message_id is None, or called locally, from test environment, when
        message_id has a value.
        """

        try:

            logging.debug(u'Receiving data from webhook')

            # step 1 -- we got message id, but no content
            #
            if not message_id:
                message_id = request.json['data']['id']

            # step 2 -- get the message itself
            #
            item = self.api.messages.get(messageId=message_id)

            # step 3 -- push it in the handling queue
            #
            self.bot.ears.put(self.normalize_message(item._json))

            return "OK"

        except Exception as feedback:
            logging.error(u"ABORTED: fatal error has been encountered")
            logging.error(feedback)
            raise

    def pull(self):
        """
        Fetches events from one Cisco Spark room

        This function senses most recent items, and pushes them
        to a processing queue.
        """

        assert self.is_ready

        logging.info(u'Pulling messages')
        self.bot.context.increment(u'puller.counter')

        assert self.api is not None  # connect() is prerequisite
        new_items = []
        try:
            items = self.api.messages.list(roomId=self.id,
                                           mentionedPeople=['me'],
                                           max=10)

            for item in items:

                if item.id == self._last_message_id:
                    break

                new_items.append(item)

        except Exception as feedback:
            logging.warning(u"Unable to pull messages")
            logging.exception(feedback)
            return

        if len(new_items):
            logging.info(u"Pulling {} new messages".format(len(new_items)))

        while len(new_items):
            item = new_items.pop()
            self._last_message_id = item.id
            self.bot.ears.put(self.normalize_message(item._json))

    def normalize_message(self, message):
        """
        Normalizes a message received from Cisco Spark

        This function adds following keys so that a neutral format
        can be used with the listener:

        * ``type`` is set to ``message``
        * ``from_id`` is a copy of ``personId``
        * ``mentioned_ids`` is a copy of ``mentionedPeople``

        """
        message['type'] = 'message'
        message['from_id'] = message.get('personId', None)
        message['mentioned_ids'] = message.get('mentionedPeople', [])
        return message
