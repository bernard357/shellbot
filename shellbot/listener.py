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

import logging
import time


class Listener(object):
    """
    Handles messages received from chat space
    """

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, bot=None, filter=None):
        """
        Handles messages received from chat space

        :param bot: the overarching bot
        :type bot: ShellBot

        :param filter: if provided, messages received are filtered
        :type filter: callable

        If a ``filter`` is provided, then it is called for each item received.

        Example::

            def filter(item):

                # duplicate input stream
                my_queue.put(item)

                # change input tream
                item['text'] = item['text'].title()

                return item

            listener = Listener(filter=filter)
        """
        self.bot = bot
        self.filter = filter

    def work(self):
        """
        Continuously receives updates

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            listener = Listener(bot=bot)

            process = Process(target=listener.work)
            process.daemon = True
            process.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            bot.context.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            bot.ears.put(Exception('EOQ'))

        """
        logging.info(u"Starting listener")

        try:
            self.bot.context.set('listener.counter', 0)
            while self.bot.context.get('general.switch', 'on') == 'on':

                if self.bot.ears.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.bot.ears.get(True, self.EMPTY_DELAY)
                    if isinstance(item, Exception):
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        logging.info(u"Listener has been stopped")

    def process(self, item):
        """
        Processes items sent by the chat space

        :param item: the message received
        :type item: dict

        This function listens for specific commands in the coming flow.
        When a command has been identified, it is responded immediately.
        Commands that require significant processing time are pushed
        to the inbox.

        This function expects following keys in each item received:

        * ``type`` -- This should have the value ``message``.
          Other values can be introduced in the future so that the listener
          has the capability to dispatch multiple events.

        * ``text`` -- This is the input coming from the chat space.

        * ``from_id`` -- This is the id of the sender of the input.
          This field allows the listener to distinguish between messages
          from the bot and messages from other chat participants.

        * ``mentioned_ids`` -- A list of targets for this input.
          This field allows the listener to determine if the input is
          explicitly for this bot or not.

        Example item received from Cisco Spark after normalization::

            {
              "id" : "Z2lzY29zcGFyazovL3VzDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/plumby use containers/docker",
              "personId" : "Y2lzY29zcGFyjOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "mentionedPeople" : ["Y2lzYDMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX"],
              "created" : "2015-10-18T14:26:16+00:00",
              "type" : "message",
              "from_id" : "Y2lzY29zcGFyjOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : ["Y2lzYDMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX"],
            }

        """
        counter = self.bot.context.increment('listener.counter')
        logging.debug(u'Listener is working on {}'.format(counter))

        try:  # sanity check
            assert item['type'] == 'message'
            input = item['text']
        except:
            logging.debug(u"- invalid format, thrown away")
            return

        if input is None:
            logging.debug(u"- no input in this item, thrown away")
            return

        if self.filter:
            item = self.filter(item)

#        print(item)

        if item['from_id'] == self.bot.context.get('bot.id'):
            logging.debug(u"- sent by me, thrown away")
            return

        if self.bot.context.get('bot.id') not in item.get('mentioned_ids', []):
            logging.info(u"- not for me, thrown away")
            return

        if len(input) > 0 and input[0] in ['@', '/', '!']:
            input = input[1:]

        bot = self.bot.context.get('bot.name', 'shelly')
        if input.lower().startswith(bot):
            input = input[len(bot):].strip()

        self.bot.shell.do(input)
