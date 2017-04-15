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

import json
import logging
import os
from multiprocessing import Process, Queue
import requests
from requests_toolbelt import MultipartEncoder
import sys
import time
from bottle import route, run, request, abort
from ciscosparkapi import CiscoSparkAPI, SparkApiError

from context import Context

class SparkSpace(object):
    """
    Handles a Cisco Spark space

    """

    def __init__(self, context, bearer=None, ears=None):
        """
        Handles a Cisco Spark space

        :param context: the general context for the full program
        :type context: Context

        :param bearer: the token used for API authentication
        :type bearer: str

        :param ears: the queue that processes incoming messages
        :type ears: Queue

        """
        self.context = context
        self.bearer = bearer
        self.ears = ears

        self.reset()

    def reset(self):
        """
        Resets a space

        After a call to this function, ``bond()`` has to be invoked again to
        return to normal mode of operation.
        """
        self.room_id = None
        self.room_title = '*unknown*'
        self.team_id = None

        self._last_message_id = 0
        self._webhook = None
        self._process = None

    def configure(self, settings):
        """
        Changes settings of the space

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

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
               'user_token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
               'webhook': "http://73a1e282.ngrok.io",
               }})

        This can also be written in a more compact form::

        >>>space.configure({'spark.room': 'My preferred room',
               'spark.token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
               })

        If a single value is provided for ``moderators`` or for ``participants``
        then it is turned automatically to a list.

        >>>space.configure({'spark.moderators': 'bobby@jah.com'})

        If ``token`` is not provided, then the function looks for an
        environment variable ``CISCO_SPARK_TOKEN`` instead.

        """

        self.context.parse(settings, 'spark', 'room', is_mandatory=True)
        self.context.parse(settings, 'spark', 'moderators')
        self.context.parse(settings, 'spark', 'participants')
        self.context.parse(settings, 'spark', 'team')
        self.context.parse(settings, 'spark', 'token')
        self.context.parse(settings, 'spark', 'personal_token')
        self.context.parse(settings, 'spark', 'webhook')

        values = self.context.get('spark.moderators')
        if isinstance(values, str):
            self.context.set('spark.moderators', [values])

        values = self.context.get('spark.participants')
        if isinstance(values, str):
            self.context.set('spark.participants', [values])

        if self.context.get('spark.personal_token') is None:
            token = os.environ.get('CISCO_SPARK_TOKEN')
            if token:
                self.context.set('spark.personal_token', token)
            else:
                logging.warning(u"Missing CISCO_SPARK_TOKEN")

        if self.context.get('spark.token') is None:
            token1 = os.environ.get('CISCO_SPARK_BOT_TOKEN')
            token2 = self.context.get('spark.personal_token')
            if token1:
                self.context.set('spark.token', token1)
            elif token2:
                self.context.set('spark.token', token2)
            else:
                logging.warning(u"Missing CISCO_SPARK_BOT_TOKEN")

        self.reset()

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

        except Exception as feedback:
            logging.warning(u"Unable to retrieve bot id")
            logging.warning(str(feedback))
            self.bot_id = None

    def bond(self,
             space,
             team=None,
             moderators=(),
             participants=(),
             hook=None):
        """
        Creates or binds to the named Cisco Spark space

        :param space: the name of the target space
        :type space: str

        :param team: the team to attach this space (optional)
        :type team: str

        :param moderators: the list of initial moderators (optional)
        :type moderators: list of str

        :param participants: the list of initial participants (optional)
        :type participants: list of str

        :param hook: an optional hook to be called (optional)
        :type hook: callable

        This function either bonds to an existing space, or creates a new space
        if necessary. In later case it also
        adds moderators and participants.

        Then it calls the optional hook. If a hook is provided, it is invoked
        with the id of the target space.
        """

        logging.info(u"Bonding to room '{}'".format(space))

        item = self.get_space(space, team)
        self.room_id = item.id
        self.room_title = item.title
        self.team_id = item.teamId

        self.add_moderators(moderators)
        self.add_participants(participants)

        if hook:
            hook(self.room_id)

    def get_space(self, space, team=None):
        """
        Gets a space by name

        :param space: name of the target space
        :type space: str

        :param team: the team to attach this space (optional)
        :type team: str or dict

        :return: a representation of the space
        :rtype: Room

        This function either returns an existing space, or creates a new one.

        >>>print(space.get_space("Hello World"))
        Room({
          "id" : "Y2lzY29zcGFyazJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
          "title" : "Hello World",
          "type" : "group",
          "isLocked" : true,
          "teamId" : "Y2lzY29zcGlNDVhZTAtYzQ2Yi0xMWU1LTlkZjktMGQ0MWUzNDIxOTcz",
          "lastActivity" : "2016-04-21T19:12:48.920Z",
          "created" : "2016-04-21T19:01:55.966Z"
        })

        If the parameter ``team`` is provided, then it can be either a simple
        name, or a team object featuring an id.

        Note: when a space already exists, but belongs to a different team, then
        only a warning message is generated in the log. This is not considered
        as an error condition.
        """
        teamId = None
        if team:
            try:
                teamId = team.id
            except:
                teamId = self.get_team(team).id

        item = self.lookup_space(space)
        if item:

            if teamId and item.teamId and (teamId != item.teamId):
                logging.warning(u"Unexpected team for this space")

            return item

        logging.info(u"Creating Cisco Spark room '{}'".format(space))

        try:
            item = self.api.rooms.create(title=space,
                                         teamId=teamId)
            logging.info(u"- done")

        except Exception as feedback:
            logging.warning(u"Unable to create room ")
            logging.warning(str(feedback))

        if teamId and item.teamId and (teamId != item.teamId):
            logging.warning(u"Unexpected team for this space")

        return item

    def lookup_space(self, space):
        """
        Looks for an existing space by name

        :param space: name of the target space
        :type space: str

        :return: attributes of the space
        :rtype: Room or None

        This function returns either an existing space, or None.

        >>>print(space.get_space("Hello World"))
        Room({
          "id" : "Y2lzY29zcGFyazJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
          "title" : "Hello World",
          "type" : "group",
          "isLocked" : true,
          "teamId" : "Y2lzY29zcGlNDVhZTAtYzQ2Yi0xMWU1LTlkZjktMGQ0MWUzNDIxOTcz",
          "lastActivity" : "2016-04-21T19:12:48.920Z",
          "created" : "2016-04-21T19:01:55.966Z"
        })

        """
        logging.info(u"Looking for Cisco Spark space '{}'".format(space))

        try:
            for item in self.api.rooms.list():
                if space == item.title:
                    logging.info(u"- found it")
                    return item

            logging.warning(u"- not found")

        except Exception as feedback:
            logging.warning(u"Unable to list rooms")
            logging.warning(str(feedback))

        return None

    def add_moderators(self, persons):
        """
        Adds multiple moderators to a space

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info(u"Adding moderators to the Cisco Spark space")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.add_moderator(person)

    def add_moderator(self, person):
        """
        Adds a moderator to a space

        :param person: e-mail address of the person to add
        :type person: str

        """
        try:
            self.api.memberships.create(roomId=self.room_id,
                                        personEmail=person,
                                        isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add moderator '{}'".format(person))
            logging.warning(str(feedback))

    def add_participants(self, persons):
        """
        Adds multiple participants to a space

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info(u"Adding participants to the Cisco Spark space")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.add_participant(person)

    def add_participant(self, person):
        """
        Adds a participant to a space

        :param person: e-mail address of the person to add
        :type person: str

        """
        try:
            self.api.memberships.create(roomId=self.room_id,
                                        personEmail=person,
                                        isModerator=True)

        except Exception as feedback:
            logging.warning(u"Unable to add participant '{}'".format(person))
            logging.warning(str(feedback))

    def dispose(self, space=None):
        """
        Deletes a Cisco Spark space

        :param space: the space to be deleted
        :type space: str or dict or None

        This function is useful to restart a clean environment.
        If no argument is provided, and if the space has been bonded
        previously, then the underlying room id is used.

        >>>space.dispose("Obsolete Space")

        or:

        >>>space.bond("Working Space")
        ...
        >>>space.dispose()

        """
        if space:
            try:
                label = space['title']
                space = space['id']
            except:
                space = self.lookup_space(space)
                if space is None:
                    return
                label = space.title
                space = space.id

        elif self.room_id:
            label = self.room_title
            space = self.room_id

        else:
            raise ValueError(u"Need to provide space to be disposed")

        logging.info(u"Deleting Cisco Spark room '{}'".format(label))

        try:
            self.api.rooms.delete(roomId=space)

            if space == self.room_id:
                self.reset()

        except Exception as feedback:
            logging.warning(u"Unable to delete room")
            logging.warning(str(feedback))

    def get_team(self, team):
        """
        Gets a team by name

        :param team: name of the target team
        :type team: str

        :return: attributes of the team
        :rtype: dict

        This function either returns an existing team, or creates a new one.

        >>>print(space.get_team("Hello World"))
        Team({
          "id" : "Y2lzY29zcGFyazovL3VzL1RFQU0Yy0xMWU2LWE5ZDgtMjExYTBkYzc5NzY5",
          "name" : "Hello World",
          "created" : "2015-10-18T14:26:16+00:00"
        })

        """
        logging.info(u"Looking for Cisco Spark team '{}'".format(team))

        for item in self.api.teams.list():
            if team == item.name:
                logging.info(u"- found it")
                return item

        logging.warning(u"- not found")
        logging.info(u"Creating Cisco Spark team'{}'".format(team))

        item = self.api.teams.create(name=team)

        logging.info(u"- done")
        return(item)

    def post_message(self,
                     text=None,
                     markdown=None,
                     file_path=None):
        """
        Posts a message for Cisco Spark

        :param markdown: content of the message as per Markdown
        :type markdown: str or list of str or ``None``

        :param text: content of the message is plain text
        :type text: str or list of str or ``None``

        :param file_path: location of file to be uploaded or attached
        :type file_path: str or ``None``

        Example message out of plain text::

        >>>space.post_message(text='hello world')
        {'text': 'hello world'}

        Example message with Markdown::

        >>>space.post_message(markdown='this is a **bold** statement')
        {'markdown': 'this is a **bold** statement'}

        Example file upload::

            space.post_message(file_path='./my_file.pdf')

        Of course, you can combine text with the upload of a file::

            text = 'This is the presentation that was used for our meeting'
            space.post_message(text=text,
                               file_path='./my_file.pdf')

        """

        logging.info(u"Posting message")

        try:
            files = [file_path] if file_path else None
            self.api.messages.create(roomId=self.room_id,
                                     text=text,
                                     markdown=markdown,
                                     files=files)
            logging.info(u"- done")


        except Exception as feedback:
            logging.warning(u"Unable to post message")
            logging.warning(str(feedback))

    def hook(self, webhook=None):
        """
        Connects in the background to Cisco Spark inbound events

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str or ``None``

        If a webhook is provided, it is registered so that Cisco Spark
        sends updates in the background. Else a daemon service is created
        in the background to pull new events.
        """
        if webhook:
            self._webhook = webhook
            self.register_hook(webhook)

        else:
            p = Process(target=self.pull_for_ever)
            p.daemon = True
            p.start()

    def unhook(self):
        pass

    def register_hook(self, webhook):
        """
        Asks Cisco Spark to send updates

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        """

        logging.info(u"Registering webhook to Cisco Spark")
        logging.info(u"- {}".format(webhook))

        try:
            self.api.webhooks.create(name='shellbot-webhook',
                                     targetUrl=webhook,
                                     resource='messages',
                                     event='created',
                                     filter='roomId='+self.room_id)

            logging.info(u"- done")

        except Exception as feedback:
            logging.warning(u"Unable to add webhook")
            logging.warning(feedback)

    def webhook():
        """
        Processes the flow of events from Cisco Spark

        This function is called from far far away, over the Internet
        """

        try:

            logging.info(u'Receiving data from webhook')

            # step 1 -- we got message id, but no content
            #
            message_id = request.json['data']['id']

            # step 2 -- get the message itself
            #
            item = self.api.messages.get(messageId=message_id)

            # step 3 -- push it in the handling queue
            #
            self.on_message(item)

            return "OK\n"

        except Exception as feedback:
            logging.error(u"ABORTED: fatal error has been encountered")
            raise

    def pull_for_ever(self):
        """
        Fetches events from one Cisco Spark space

        This function senses new items at regular intervals, and pushes them
        to a processing queue.
        """

        logging.info(u'Starting puller')

        try:
            self.context.set('puller.counter', 0)
            while self.context.get('general.switch', 'on') == 'on':

                self.pull()
                time.sleep(1)

        except KeyboardInterrupt:
            pass

        logging.info(u"Puller has been stopped")

    def pull(self):
        """
        Fetches events from one Cisco Spark space

        This function senses most recent items, and pushes them
        to a processing queue.
        """

        logging.info(u'Pulling messages')
        self.context.increment(u'puller.counter')

        new_items = []
        try:
            items = self.api.messages.list(roomId=self.room_id,
                                           mentionedPeople=['me'],
                                           max=10)

            for item in items:

                if item.id == self._last_message_id:
                    break

                new_items.append(item)

        except Exception as feedback:
            logging.warning(u"Unable to pull messages")
            logging.warning(str(feedback))
            return

        if len(new_items):
            logging.info(u"Pulling {} new messages".format(len(new_items)))

        while len(new_items):
            item = new_items.pop()
            self._last_message_id = item.id
            self.on_message(message=item)

    def on_message(self, message):
        """
        Processes an incoming message
        """
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

        logging.info(u"- done")
        return item
