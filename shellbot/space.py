#!/usr/bin/env python
import json
import logging
import os
from multiprocessing import Process, Queue
import requests
from requests_toolbelt import MultipartEncoder
import sys
import time
from bottle import route, run, request, abort
from ciscosparkapi import CiscoSparkAPI

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
        self.bearer = bearer if bearer else None
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

        self.api = CiscoSparkAPI(access_token=self.bearer)

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
        :type team: str or dict

        :param moderators: the list of initial moderators (optional)
        :type moderators: list of str

        :param participants: the list of initial participants (optional)
        :type participants: list of str

        :param hook: an optional hook to be called on space creation (optional)
        :type hook: callable

        This function either bonds to an existing space, or creates a new space
        if necessary. In later case it also
        adds moderators and participants, then calls the optional hook.

        If a hook is provided, it is invoked with the id of the target space.
        """
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

        :return: attributes of the space
        :rtype: dict

        This function either returns an existing space, or creates a new one.

        >>>print(space.get_space("Hello World"))
        {
          "id" : "Y2lzY29zcGFyazJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
          "title" : "Hello World",
          "type" : "group",
          "isLocked" : true,
          "teamId" : "Y2lzY29zcGlNDVhZTAtYzQ2Yi0xMWU1LTlkZjktMGQ0MWUzNDIxOTcz",
          "lastActivity" : "2016-04-21T19:12:48.920Z",
          "created" : "2016-04-21T19:01:55.966Z"
        }

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
                logging.warning("Unexpected team for this space")

            return item

        logging.info("Creating Cisco Spark space '{}'".format(space))
        item = self.api.rooms.create(title=space,
                                     teamId=teamId)
        logging.info("- done")

        if teamId and item.teamId and (teamId != item.teamId):
            logging.warning("Unexpected team for this space")

        return item

    def lookup_space(self, space):
        """
        Looks for an existing space by name

        :param space: name of the target space
        :type space: str

        :return: attributes of the space
        :rtype: dict or None

        This function returns either an existing space, or None.

        >>>print(space.get_space("Hello World"))
        {
          "id" : "Y2lzY29zcGFyazJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
          "title" : "Hello World",
          "type" : "group",
          "isLocked" : true,
          "teamId" : "Y2lzY29zcGlNDVhZTAtYzQ2Yi0xMWU1LTlkZjktMGQ0MWUzNDIxOTcz",
          "lastActivity" : "2016-04-21T19:12:48.920Z",
          "created" : "2016-04-21T19:01:55.966Z"
        }

        """
        logging.info("Looking for Cisco Spark space '{}'".format(space))

        for item in self.api.rooms.list():
            if space == item.title:
                logging.info("- found it")
                return item

        logging.warning("- not found")
        return None

    def add_moderators(self, persons):
        """
        Adds multiple moderators to a space

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info("Adding moderators to the Cisco Spark space")
        for person in persons:
            logging.info("- {}".format(person))
            self.add_moderator(person)

    def add_moderator(self, person):
        """
        Adds a moderator to a space

        :param person: e-mail address of the person to add
        :type person: str

        """
        self.api.memberships.create(roomId=self.room_id,
                                    personEmail=person,
                                    isModerator=True)

    def add_participants(self, persons):
        """
        Adds multiple participants to a space

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info("Adding participants to the Cisco Spark space")
        for person in persons:
            logging.info("- {}".format(person))
            self.add_participant(person)

    def add_participant(self, person):
        """
        Adds a participant to a space

        :param person: e-mail address of the person to add
        :type person: str

        """
        self.api.memberships.create(roomId=self.room_id,
                                    personEmail=person,
                                    isModerator=True)

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
                label = space['title']
                space = space['id']

        elif self.room_id:
            label = self.room_title
            space = self.room_id

        else:
            raise ValueError("Need to provide space to be disposed")

        logging.info("Deleting Cisco Spark space '{}'".format(label))

        self.api.rooms.delete(roomId=space)

        if space == self.room_id:
            self.reset()

    def get_team(self, team):
        """
        Gets a team by name

        :param team: name of the target team
        :type team: str

        :return: attributes of the team
        :rtype: dict

        This function either returns an existing team, or creates a new one.

        >>>print(space.get_team("Hello World"))
        {
          "id" : "Y2lzY29zcGFyazovL3VzL1RFQU0Yy0xMWU2LWE5ZDgtMjExYTBkYzc5NzY5",
          "name" : "Hello World",
          "created" : "2015-10-18T14:26:16+00:00"
        }

        """
        logging.info("Looking for Cisco Spark team '{}'".format(team))

        for item in self.api.teams.list():
            if team == item.name:
                logging.info("- found it")
                return item

        logging.warning("- not found")
        logging.info("Creating Cisco Spark team'{}'".format(team))

        item = self.api.teams.create(name=team)

        logging.info("- done")
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

        logging.info("Posting message")

        files = [file_path] if file_path else None
        self.api.messages.create(roomId=self.room_id,
                                 text=text,
                                 markdown=markdown,
                                 files=files)

        logging.info("- done")

    def connect(self, webhook=None):
        """
        Connects in the background to Cisco Spark inbound events

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str or ``None``

        If a webhook is provided, it is registered so that Cisco Spark
        sends updates in the background. Else a daemon service is created
        in the background to pull new events.
        """
        if webhook:
            self.register_hook(webhook)

        else:
            p = Process(target=self.pull_for_ever)
            p.daemon = True
            p.start()

    def register_hook(self, webhook):
        """
        Asks Cisco Spark to send updates

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        """

        logging.info("Registering webhook to Cisco Spark")
        logging.info("- {}".format(webhook))

        self.api.webhooks.create(name='shellbot-webhook',
                                 targetUrl=webhook,
                                 resource='messages',
                                 event='created',
                                 filter='roomId='+self.room_id)

        logging.info("- done")

    def webhook():
        """
        Processes the flow of events from Cisco Spark

        This function is called from far far away, over the Internet
        """

        try:

            logging.info('Receiving data from webhook')

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
            logging.error("ABORTED: fatal error has been encountered")
            raise

    def pull_for_ever(self):
        """
        Fetches events from one Cisco Spark space

        This function senses new items at regular intervals, and pushes them
        to a processing queue.
        """

        logging.info('Looping for new messages')

        self.context.set('puller.counter', 0)
        while self.context.get('general.switch', 'on') == 'on':

            self.pull()
            time.sleep(1)

    def pull(self):
        """
        Fetches events from one Cisco Spark space

        This function senses most recent items, and pushes them
        to a processing queue.
        """

        logging.info('Pulling messages pro-actively')
        self.context.increment('puller.counter')

        new_items = []
        for item in self.api.messages.list(roomId= self.room_id,
                                           max=25):

            if item.id == self._last_message_id:
                break

            new_items.append(item)

        if len(new_items):
            logging.info("Fetching {} new messages".format(len(new_items)))

        while len(new_items):
            item = new_items.pop()
            self._last_message_id = item.id
            self.on_message(message=item)

    def on_message(self, message):
        """
        Processes an incoming message
        """
        self.ears.put(message.text)

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
        logging.info("Getting bot attributes")

        item = self.api.people.me()

        logging.info("- done")
        return item
