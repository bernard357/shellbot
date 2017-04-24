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
from ciscosparkapi import CiscoSparkAPI

from shellbot import Context
from .base import Space


class SparkSpace(Space):
    """
    Handles a Cisco Spark room
    """

    def on_init(self,
                ex_token=None,
                ex_ears=None,
                **kwargs):
        """
        Handles extended initialisation parameters

        :param ex_token: authentication token for the Cisco Spark API

        :param ex_ears: queue for inbound messages

        """
        self.prefix = 'spark'
        self.token = ex_token
        self.ears = ex_ears if ex_ears else Queue

    def on_reset(self):
        """
        Resets extended internal variables
        """
        self.teamId = None

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
        values = self.context.get('spark.moderators')
        if isinstance(values, string_types):
            self.context.set('spark.moderators', [values])

        values = self.context.get('spark.participants')
        if isinstance(values, string_types):
            self.context.set('spark.participants', [values])

        if self.context.get('spark.personal_token') is None:
            token = os.environ.get('CISCO_SPARK_TOKEN')
            if token:
                self.context.set('spark.personal_token', token)

        if self.context.get('spark.token') is None:
            token1 = os.environ.get('CISCO_SPARK_BOT_TOKEN')
            token2 = self.context.get('spark.personal_token')
            if token1:
                self.context.set('spark.token', token1)
            elif token2:
                self.context.set('spark.token', token2)

        self.context.check('spark.room', is_mandatory=True)
        self.context.check('spark.moderators', [])
        self.context.check('spark.participants', [])
        self.context.check('spark.team')
        self.context.check('spark.token', filter=True)
        self.context.check('spark.personal_token', filter=True)

    def connect(self):
        """
        Connects to the back-end API
        """
        token = self.bearer if self.bearer else self.context.get('spark.token')
        try:
            if token is None:
                self.api = None
                logging.error(u"Unable to access Cisco Spark API")

            else:
                self.api = CiscoSparkAPI(access_token=token)
                logging.debug(u"Connected as bot to Cisco Spark API")

        except Exception as feedback:
            logging.error(u"Unable to access Cisco Spark API")
            logging.error(u"- {}".format(str(feedback)))
            logging.error(u"- token '{}'".format(token))

        token = self.context.get('spark.personal_token')
        try:
            if token is None:
                self.personal_api = None
            else:
                self.personal_api = CiscoSparkAPI(access_token=token)
                logging.debug(u"Connected as person to Cisco Spark API")

        except Exception as feedback:
            logging.error(u"Unable to access Cisco Spark API")
            logging.error(u"- {}".format(str(feedback)))
            logging.error(u"- token '{}'".format(token))

        try:
            bot = self.get_bot()
            self.context.set('bot.name', str(bot.displayName.split(' ')[0]))
            logging.debug(u"Bot name: {}".format(self.context.get('bot.name')))

            self.bot_id = bot.id
            self.context.set('bot.id', bot.id)

        except Exception as feedback:
            logging.warning(u"Unable to retrieve bot id")
            logging.warning(str(feedback))
            self.bot_id = None

    def lookup_space(self, title):
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

        try:
            for room in self.api.rooms.list():
                if title == room.title:
                    logging.info(u"- found it")
                    self.use_room(room)
                    return True

            logging.info(u"- not found")

        except Exception as feedback:
            logging.error(u"Unable to list rooms")
            logging.error(feedback)

        return False

    def create_space(self, title, ex_team=None):
        """
        Creates a space

        :param title: title of the target space
        :type title: str

        :param ex_team: the team attached to this room (optional)
        :type ex_team: str or object

        On successful space creation, the object should be initialised
        to use it.

        If the parameter ``ex_team`` is provided, then it can be either a
        simple name, or a team object featuring an id.
        """
        teamId = None
        if ex_team:
            try:
                teamId = ex_team.id
            except:
                teamId = self.get_team(ex_team).id

        logging.info(u"Creating Cisco Spark room '{}'".format(title))

        try:
            room = self.api.rooms.create(title=title,
                                         teamId=teamId)
            logging.info(u"- done")

            self.use_room(room)

        except Exception as feedback:
            logging.warning(u"Unable to create room ")
            logging.warning(feedback)

    def use_room(self, room):
        """
        Uses this room for this space

        :param room: the representation to use

        """
        logging.info(u"Bonding to room '{}'".format(room.title))
        self.id = room.id
        self.context.set(self.prefix+'.id', self.id)
        logging.debug(u"- id: {}".format(self.id))

        self.title = room.title
        self.context.set(self.prefix+'.title', self.title)
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
        try:
            self.api.memberships.create(roomId=self.id,
                                        personEmail=person,
                                        isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add moderator '{}'".format(person))
            logging.warning(feedback)

    def add_participant(self, person):
        """
        Adds a participant

        :param person: e-mail address of the person to add
        :type person: str

        """
        try:
            self.api.memberships.create(roomId=self.id,
                                        personEmail=person,
                                        isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add participant '{}'".format(person))
            logging.warning(feedback)

    def delete_space(self, title=None, **kwargs):
        """
        Deletes a Cisco Spark room

        :param title: title of the room to be deleted (optional)
        :type title: str

        >>>space.delete_space("Obsolete Space")

        """
        if title and self.lookup_space(title=title):
            pass

        elif self.id and self.title:
            pass

        elif (self.context.get(self.prefix+'.title')
              and self.lookup_space(
                    title=self.context.get(self.prefix+'.title'))):
            pass

        else:
            raise ValueError(u"unable to find a room to delete")

        logging.info(u"Deleting Cisco Spark room '{}'".format(self.title))

        try:
            self.api.rooms.delete(roomId=self.id)

        except Exception as feedback:
            logging.warning(u"Unable to delete room")
            logging.warning(feedback)

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
            self.id = self.context.get(self.prefix+'.id')

        logging.debug(u"- text: {}".format(text))

        try:
            files = [ex_file_path] if ex_file_path else None
            self.api.messages.create(roomId=self.id,
                                     text=text,
                                     markdown=ex_markdown,
                                     files=files)
            logging.debug(u"- done")

        except Exception as feedback:
            logging.warning(u"Unable to post message")
            logging.warning(feedback)

    def register(self, webhook):
        """
        Connects in the background to Cisco Spark inbound events

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        This function registers the provided hook to Cisco Spark.
        """
        assert webhook is not None

        logging.info(u"Registering webhook to Cisco Spark")
        logging.debug(u"- {}".format(webhook))

        try:
            self.api.webhooks.create(name='shellbot-webhook',
                                     targetUrl=webhook,
                                     resource='messages',
                                     event='created',
                                     filter='roomId='+self.id)

            logging.debug(u"- done")

        except Exception as feedback:
            logging.warning(u"Unable to add webhook")
            logging.warning(feedback)

    def webhook(self):
        """
        Processes the flow of events from Cisco Spark

        This function is called from far far away, over the Internet
        """

        try:

            logging.debug(u'Receiving data from webhook')

            # step 1 -- we got message id, but no content
            #
            message_id = request.json['data']['id']

            # step 2 -- get the message itself
            #
            item = self.api.messages.get(messageId=message_id)

            # step 3 -- push it in the handling queue
            #
            self.ears.put(item._json)

            return "OK\n"

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

        logging.info(u'Pulling messages')
        self.context.increment(u'puller.counter')

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
            logging.warning(feedback)
            return

        if len(new_items):
            logging.info(u"Pulling {} new messages".format(len(new_items)))

        while len(new_items):
            item = new_items.pop()
            self._last_message_id = item.id
            self.ears.put(message._json)

    def get_bot(self):
        """
        Retrieves attributes of this bot

        :return: the attributes as returned from Cisco Spark
        :rtype: Person

        >>>print(space.get_bot())
        Person({"displayName": "handy (bot)",
                "created": "2016-10-15T14:55:54.739Z",
                "emails": ["handy@sparkbot.io"],
                "orgId": "Y2lzY29zcGFyazovL3VzL09SR0FOSVpZS00ODYzY2NmNzIzZDU",
                "avatar": "https://2b571e1108a5262.cdn.com/V1~6bg==~80",
                "type": "bot",
                "id": "Y2lzY29zcGFyazovL3mI4LTQ1MDktYWRkMi0yNTEwNzdlOWUxZWM"})

        """
        logging.info(u"Getting bot attributes")

        item = self.api.people.me()

        logging.debug(u"- done")
        return item
