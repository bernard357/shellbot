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

    def __init__(self, context, bearer, ears=None):
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

    def dispose(self, space):
        """
        Deletes a Cisco Spark space by name

        :param space: the name of the space to be deleted
        :type space: str

        This function is useful to restart a clean demo environment
        """

        print("Deleting Cisco Spark space '{}'".format(space))

        url = 'https://api.ciscospark.com/v1/rooms'
        headers = {'Authorization': 'Bearer '+self.bearer}
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            print(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        actual = False
        for item in response.json()['items']:

            if space in item['title']:
                print("- found it")
                print("- DELETING IT")

                url = 'https://api.ciscospark.com/v1/rooms/'+item['id']
                headers = {'Authorization': 'Bearer '+self.bearer}
                response = requests.delete(url=url, headers=headers)

                if response.status_code != 204:
                    raise Exception("Received error code {}".format(
                        response.status_code))

                actual = True

        if not actual:
            print("- no space with this name has been found")

        self.room_id = None

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

        print("Looking for Cisco Spark space '{}'".format(space))

        url = 'https://api.ciscospark.com/v1/rooms'
        headers = {'Authorization': 'Bearer '+self.bearer}
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            print(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        for item in response.json()['items']:
            if space in item['title']:
                print("- found it")
                self.room_id = item['id']
                return

        print("- not found")
        print("Creating Cisco Spark space'{}'".format(space))

        url = 'https://api.ciscospark.com/v1/rooms'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'title': space }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            print(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        print("- done")
        self.room_id = response.json()['id']

        print("Adding moderators to the Cisco Spark space")

        for item in moderators:
            print("- {}".format(item))
            self.add_person(self.room_id, person=item, isModerator='true')

        print("Adding participants to the Cisco Spark space")

        for item in participants:
            print("- {}".format(item))
            self.add_person(self.room_id, person=item)

        print("Getting bot id")

        url = 'https://api.ciscospark.com/v1/people/me'
        headers = {'Authorization': 'Bearer '+self.bearer}
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            print(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        print("- done")
        context.set('bot.id', response.json()['id'])

        if hook:
            hook()

    def add_person(self, person=None, isModerator='false'):
        """
        Adds a person to a space

        :param person: e-mail address of the person to add
        :type person: str

        :param isModerator: for moderators
        :type isModerator: bool

        """

        url = 'https://api.ciscospark.com/v1/memberships'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'roomId': self.room_id,
                   'personEmail': person,
                   'isModerator': isModerator }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            print(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

    def build_message(self,
                      markdown=None,
                      text=None,
                      file_path=None,
                      file_label=None,
                      file_type=None):
        """
        Prepares a message for Cisco Spark

        :param markdown: content of the message as per Markdown
        :type markdown: str or ``None``

        :param text: content of the message is plain text
        :type text: str or ``None``

        :param file_path: location of file to be uploaded
        :type file_path: str or ``None``

        :param file_label: optional label for the file instead of file name
        :type file_path: str or ``None``

        :param file_type: optional MIME type for the file instead of default
        :type file_type: str or ``None``

        :return: the message to be posted
        :rtype: str or dict

        Example message out of plain text:

        >>>space.build_message(text='hello world')

        Example message with Markdown:

        >>>space.build_message(markdown='this is a **bold** statement')

        Example file upload:
        >>>space.build_message(file_path='./my_file.pdf', file_label='pres')

        Of course, you can combine text with the upload of a file:

        >>>text = 'This is the presentation that was used for our meeting'
        >>>file_path = './my_file.pdf'
        >>>file_label = 'pres from Foo Bar'
        >>>space.build_message(text=text, file_path=file_path, file_label=file_label)
        """

        print("Building message")

        update = {}

        # textual message
        #
        if markdown:

            text = 'using markdown content'
            update['markdown'] = markdown

        elif text:

            text = "'{}".format(text)
            update['text'] = text

        # file upload
        #
        if file_path:

            print("- attaching file {}".format(file_path))

            if file_label is None:
                file_label = file_path

            elif 'text' not in update:
                update['text'] = "'{}'".format(file_label)

            if file_type is None:
                file_type = 'application/octet-stream'

            update['files'] = (file_label, open(file_path, 'rb'), file_type)

        return update

    def post_message(self, message):
        """
        Sends a meessage to a Cisco Spark space

        :param message: the message to be sent
        :type message: str or dict

        If the message is a simple string, it is sent as such to Cisco Spark.
        Else if it a dictionary, it is encoded as MIME Multipart.
        """

        print("Sending update to Cisco Spark room")

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
            print("Sender received error code {}".format(response.status_code))

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
            w = Process(target=self.pull_for_ever)
            w.daemon = True
            w.start()

    def register_hook(self, webhook):
        """
        Asks Cisco Spark to send updates

        :param webhook: web address to be used by Cisco Spark service
        :type webhook: str

        """

        print("Registering webhook to Cisco Spark")
        print("- {}".format(url))

        url = 'https://api.ciscospark.com/v1/webhooks'
        headers = {'Authorization': 'Bearer '+self.bearer}
        payload = {'name': 'controller-webhook',
                   'resource': 'messages',
                   'event': 'created',
                   'filter': 'roomId='+self.room_id,
                   'targetUrl': webhook }
        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            print(response.json())
            raise Exception("Received error code {}".format(
                response.status_code))

        print("- done")

    def on_message():
        """
        Processes the flow of events from Cisco Spark

        This function is called from far far away, over the Internet
        """

        try:

            print('Receiving data from webhook')

            # step 1 -- we got message id, but no content
            #
            message_id = request.json['data']['id']

            # step 2 -- get the message itself
            #
            url = 'https://api.ciscospark.com/v1/messages/{}'.format(message_id)
            headers = {'Authorization': 'Bearer '+self.bearer}
            response = requests.get(url=url, headers=headers)

            if response.status_code != 200:
                print("Received error code {}".format(response.status_code))
                print(response.json())
                raise Exception

            # step 3 -- push it in the handling queue
            #
            self.ears.put(response.json())

            return "OK\n"

        except Exception as feedback:
            print("ABORTED: fatal error has been encountered")
            raise

    def pull_for_ever(self):
        """
        Fetches events from one Cisco Spark space

        This function senses new items at regular intervals, and pushes them
        to a processing queue.
        """

        print('Pulling messages pro-actively')

        last_id = 0
        while context.get('general.switch', 'on') == 'on':

            time.sleep(1)

            try:
                url = 'https://api.ciscospark.com/v1/messages'
                headers = {'Authorization': 'Bearer '+self.bearer}
                payload = {'roomId': self.room_id, 'max': 10 }
                response = requests.get(url=url,
                                        headers=headers,
                                        params=payload)

                if response.status_code == 403:
                    print("Received error code {}".format(
                        response.status_code))
                    print(response.json())
                    continue

                if response.status_code != 200:
                    print("Received error code {}".format(
                        response.status_code))
                    print(response.json())
                    raise Exception

                items = response.json()['items']

                index = 0
                while index < len(items):
                    if items[index]['id'] == last_id:
                        break
                    index += 1

                if index > 0:
                    print("Fetching {} new messages".format(index))

                while index > 0:
                    index -= 1
                    last_id = items[index]['id']
                    self.ears.put(items[index])

            except Exception as feedback:
                print("ERROR: exception raised while fetching messages")
                raise

