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

from context import Context

class SparkSpace(object):
    """
    Handles a Cisco Spark space

    """

    def __init__(self, context, bearer=None, ears=None):
        """
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

        self.room_id = None

        self._last_message_id = 0

    def bond(self, space, teams=(), moderators=(), participants=(), hook=None):
        """
        Creates or binds to the named Cisco Spark space

        :param space: the name of the target space
        :type space: str

        :param teams: the list of teams for this space
        :type teams: list of str

        :param moderators: the list of initial moderators
        :type moderators: list of str

        :param participants: the list of initial participants
        :type participants: list of str

        :param hook: an optional hook to be called on space creation
        :type hook: function

        This function creates a new space if necessary. In that case it also
        adds moderators and participants, then calls the optional hook.
        """

        logging.info("Looking for Cisco Spark space '{}'".format(space))

        url = 'https://api.ciscospark.com/v1/rooms'
        headers = {'Authorization': 'Bearer '+self.bearer}
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        for item in response.json()['items']:
            if space in item['title']:
                logging.info("- found it")
                self.room_id = item['id']
                return

        logging.debug("- not found")
        logging.info("Creating Cisco Spark space'{}'".format(space))

        url = 'https://api.ciscospark.com/v1/rooms'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'title': space }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        logging.info("- done")
        self.room_id = response.json()['id']

        self.add_moderators(moderators)

        self.add_participants(participants)

        context.set('bot.id', self.get_bot_id())

        if hook:
            hook()

    def get_bot_id(self):
        """
        Retrieves the id of this bot

        :return: the bot id as returned from Cisco Spark
        :rtype: str

        """
        logging.info("Getting bot id")

        url = 'https://api.ciscospark.com/v1/people/me'
        headers = {'Authorization': 'Bearer '+self.bearer}
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        logging.info("- done")
        return response.json()['id']

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

        url = 'https://api.ciscospark.com/v1/memberships'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'roomId': self.room_id,
                   'personEmail': person,
                   'isModerator': 'true' }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

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

        url = 'https://api.ciscospark.com/v1/memberships'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'roomId': self.room_id,
                   'personEmail': person,
                   'isModerator': 'false' }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

    def dispose(self, space):
        """
        Deletes a Cisco Spark space by name

        :param space: the name of the space to be deleted
        :type space: str

        This function is useful to restart a clean demo environment
        """

        logging.info("Deleting Cisco Spark space '{}'".format(space))

        url = 'https://api.ciscospark.com/v1/rooms'
        headers = {'Authorization': 'Bearer '+self.bearer}
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        actual = False
        for item in response.json()['items']:

            if space in item['title']:
                logging.info("- found it")
                logging.info("- DELETING IT")

                url = 'https://api.ciscospark.com/v1/rooms/'+item['id']
                headers = {'Authorization': 'Bearer '+self.bearer}
                response = requests.delete(url=url, headers=headers)

                if response.status_code != 204:
                    logging.error(response.json())
                    raise Exception("Received error code {}".format(
                        response.status_code))

                actual = True

        if not actual:
            logging.info("- no space with this name has been found")

        self.room_id = None

    @classmethod
    def build_message(self,
                      markdown=None,
                      text=None,
                      file_path=None,
                      file_label=None,
                      file_type=None):
        """
        Prepares a message for Cisco Spark

        :param markdown: content of the message as per Markdown
        :type markdown: str or list of str or ``None``

        :param text: content of the message is plain text
        :type text: str or list of str or ``None``

        :param file_path: location of file to be uploaded
        :type file_path: str or ``None``

        :param file_label: optional label for the file instead of file name
        :type file_path: str or ``None``

        :param file_type: optional MIME type for the file instead of default
        :type file_type: str or ``None``

        :return: the message to be posted
        :rtype: dict

        Example message out of plain text::

        >>>space.build_message(text='hello world')
        {'text': 'hello world'}

        Lists of messages are combined as one::

        >>>space.build_message(text=['hello', 'world'])
        {'text': 'hello\nworld'}

        Example message with Markdown::

        >>>space.build_message(markdown='this is a **bold** statement')
        {'markdown': 'this is a **bold** statement'}

        Lists of Markdown messages are combined as one as well::

        >>>space.build_message(markdown=['* line 1', '* line 2'])
        {'markdown': '* line 1\n* line 2'}

        Example file upload::

            space.build_message(file_path='./my_file.pdf', file_label='pres')

        Of course, you can combine text with the upload of a file::

            text = 'This is the presentation that was used for our meeting'
            space.build_message(text=text,
                                file_path='./my_file.pdf',
                                file_label='pres from Foo Bar')

        """

        logging.info("Building message")

        update = {}

        if isinstance(text, (list, tuple)):
            update['text'] = '\n'.join(text)

        elif text:
            update['text'] = str(text)

        if isinstance(markdown, (list, tuple)):
            update['markdown'] = '\n'.join(markdown)

        elif markdown:
            update['markdown'] = markdown

        if file_path:

            logging.info("- attaching file {}".format(file_path))

            if file_label is None:
                file_label = file_path

            elif 'text' not in update:
                update['text'] = str(file_label)

            if file_type is None:
                file_type = 'application/octet-stream'

            update['files'] = (file_label, open(file_path, 'rb'), file_type)

        if update == {}:
            update = {'text': ''}

        return update

    def post_message(self, message):
        """
        Sends a meessage to a Cisco Spark space

        :param message: the message to be sent
        :type message: str or dict

        If the message is a simple string, it is sent as such to Cisco Spark.
        Else if it a dictionary, it is encoded as MIME Multipart.
        """

        logging.info("Sending update to Cisco Spark room")

        url = 'https://api.ciscospark.com/v1/messages'
        headers = {'Authorization': 'Bearer '+self.bearer}

        if isinstance(message, dict):
            message['roomId'] = self.room_id
            payload = MultipartEncoder(fields=message)
            headers['Content-Type'] = payload.content_type
        else:
            payload = {'roomId': self.room_id, 'text': str(message) }

        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Error on post: {}".format(
                response.status_code))

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

        url = 'https://api.ciscospark.com/v1/webhooks'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'name': 'controller-webhook',
                   'resource': 'messages',
                   'event': 'created',
                   'filter': 'roomId='+self.room_id,
                   'targetUrl': webhook }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Error on register: {}".format(
                response.status_code))

        logging.info("- done")

    def on_message():
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
            url = 'https://api.ciscospark.com/v1/messages/{}'.format(message_id)
            headers = {'Authorization': 'Bearer '+self.bearer}
            response = requests.get(url=url, headers=headers)

            if response.status_code != 200:
                logging.error("Received error code {}".format(response.status_code))
                logging.error(response.json())
                raise Exception

            # step 3 -- push it in the handling queue
            #
            self.ears.put(response.json())

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

        url = 'https://api.ciscospark.com/v1/messages'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'roomId': self.room_id, 'max': 10 }
        response = requests.get(url=url,
                                headers=headers,
                                params=payload)

        if response.status_code == 403:
            logging.error("Error on pull: {}".format(
                response.status_code))
            logging.error(response.json())
            return

        if response.status_code != 200:
            logging.error(response.json())
            raise Exception("Error on pull: {}".format(
                response.status_code))

        items = response.json()['items']

        index = 0
        while index < len(items):
            if items[index]['id'] == self._last_message_id:
                break
            index += 1

        if index > 0:
            logging.info("Fetching {} new messages".format(index))

        while index > 0:
            index -= 1
            self._last_message_id = items[index]['id']
            self.ears.put(items[index])
