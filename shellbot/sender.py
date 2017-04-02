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

import logging
from Queue import Empty
import requests
from requests_toolbelt import MultipartEncoder
import random
import time

class Sender(object):
    """
    Sends updates to Cisco Spark
    """

    def __init__(self, mouth):
        self.mouth = mouth

    def work(self, context):
        print("Starting sender")

        self.context = context

        self.context.set('sender.counter', 0)
        while self.context.get('general.switch', 'on') == 'on':
            try:
                item = self.mouth.get(True, 0.1)
                if isinstance(item, Exception):
                    break
                counter = self.context.increment('sender.counter')
                self.process(item, counter)
            except Empty:
                pass

    def process(self, item, counter):
        """
        Sends one update to Cisco Spark
        """

        print('Sender is working on {}'.format(counter))

        update = self.build_update(item, counter)
        self.post_update(update)


    def build_update(self, item, counter):
        """
        Prepares an update that can be read by human beings

        :return: the update to be posted
        :rtype: ``str`` or ``dict`

        The action can be either:

        * send a text message to the room with `text:` statement
        * send a Markdown message to the room with `markdown:` statement
        * upload a file with `file:`, `label:` and `type:`
        * send a message and attach a file


        """

        print("Building update")

        # sanity check
        #
        if not isinstance(item, dict):
            return item

        # now build the update snippet as expected by Cisco Spark
        #
        update = {}

        # textual message
        #
        if 'markdown' in item:

            text = 'using markdown content'
            update['markdown'] = item['markdown']

        elif 'message' in item:

            text = "'{}".format(item['message'])
            update['text'] = item['message']

        # file upload
        #
        if 'file' in item:

            print("- attaching file {}".format(item['file']))

            if 'label' in item:
                text = item['label']

                if 'text' not in update:
                    update['text'] = "'{}'".format(item['label'])

            else:
                text = item['file']

            if 'type' in item:
                type = item['type']
            else:
                type = 'application/octet-stream'

            update['files'] = (text, open(item['file'], 'rb'), type)

        return update

    def post_update(self, update):
        """
        Updates a Cisco Spark room

        If the update is a simple string, it is sent as such to Cisco Spark.
        Else if it a dictionary, then it is encoded as MIME Multipart.
        """

        print("Sending update to Cisco Spark room")

        bearer = self.context.get('spark.CISCO_SPARK_PLUMBERY_BOT', '')
        room_id = self.context.get('spark.room_id', '')

        url = 'https://api.ciscospark.com/v1/messages'
        headers = {'Authorization': 'Bearer '+bearer}

        if isinstance(update, dict):
            update['roomId'] = room_id
            payload = MultipartEncoder(fields=update)
            headers['Content-Type'] = payload.content_type
        else:
            payload = {'roomId': room_id, 'text': update }

        response = requests.post(url=url, headers=headers, data=payload)

        if response.status_code != 200:
            print("Sender received error code {}".format(response.status_code))
