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

    def __init__(self, bot=None, tee=None):
        """
        Handles messages received from chat space

        :param bot: the overarching bot
        :type bot: ShellBot

        :param tee: if provided, messages received are duplicated there
        :type tee: queue

        """
        self.bot = bot
        self.context = bot.context
        self.ears = bot.ears
        self.shell = bot.shell

        self.tee = tee

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
            self.context.set('listener.counter', 0)
            while self.context.get('general.switch', 'on') == 'on':

                if self.ears.empty():
                    time.sleep(0.005)
                    continue

                try:
                    item = self.ears.get(True, 0.1)
                    if isinstance(item, Exception):
                        break
                    counter = self.context.increment('listener.counter')

                    if self.tee:
                        self.tee.put(item)

                    self.process(item, counter)

                except Exception as feedback:
                    logging.debug(feedback)
                    break

        except KeyboardInterrupt:
            pass

        logging.info(u"Listener has been stopped")

    def process(self, item, counter):
        """
        Processes bits coming from Cisco Spark

        :param item: the message received
        :type item: dict

        :param counter: number of items processed so far
        :type counter: int

        This function listens for specific commands in the coming flow.
        When a command has been identified, it is acknowledged immediately.
        Commands that require significant processing time are pushed
        to the inbox.

        Example command received from Cisco Spark:

            {
              "id" : "Z2lzY29zcGFyazovL3VzDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "roomId" : "Y2lzY29zcGFyazovNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/plumby use containers/docker",
              "personId" : "Y2lzY29zcGFyjOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "created" : "2015-10-18T14:26:16+00:00",
            }

        """
        logging.debug(u'Listener is working on {}'.format(counter))

        # sanity check
        #
        try:
            input = item['text']
        except:
            logging.debug(u"- invalid format, thrown away")
            return

        if input is None:
            logging.debug(u"- no input in this item, thrown away")
            return

        # my own messages
        #
        if item['personId'] == self.context.get('bot.id'):
            logging.debug(u"- sent by me, thrown away")
            return

#        print(item)

        # we can be called with 'plumby ...' or '@plumby ...' or '/plumby ...'
        #
        if input[0] in ['@', '/']:
            input = input[1:]

        bot = self.context.get('bot.name', 'shelly')
        if not input.lower().startswith(bot):
            try:
                logging.debug(u"- {}".format(input))
            except:
                pass
            logging.info(u"- not for me, thrown away")
            return

        line = input[len(bot):].strip()

        self.shell.do(line)
