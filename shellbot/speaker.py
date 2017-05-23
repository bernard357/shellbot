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
from multiprocessing import Process, Queue
from six import string_types
import time


class Speaker(object):
    """
    Sends updates to a business messaging space
    """

    EMPTY_DELAY = 0.005   # time to wait if queue is empty
    NOT_READY_DELAY = 5   # time to wait if space is not ready

    def __init__(self, bot=None):
        """
        Sends updates to a business messaging space

        :param bot: the overarching bot
        :type bot: ShellBot

        """
        self.bot = bot

    def run(self):
        """
        Starts the speaking process

        :return: either the process that has been started, or None

        This function starts a separate daemonic process to speak
        in the background.
        """
        p = Process(target=self.work)
        p.daemon = True
        p.start()
        return p

    def work(self):
        """
        Continuously send updates

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            speaker = Speaker(bot=bot)

            process = Process(target=speaker.work)
            process.daemon = True
            process.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            bot.context.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            bot.mouth.put(Exception('EOQ'))

        Note that items are not picked up from the queue until the underlying
        space is ready for handling messages.
        """
        logging.info(u"Starting speaker")

        try:
            self.bot.context.set('speaker.counter', 0)
            not_ready_flag = True
            while self.bot.context.get('general.switch', 'on') == 'on':

                if self.bot.mouth.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                if not self.bot.space.is_ready:
                    if not_ready_flag:
                        logging.debug(
                            u"Speaker is waiting for space to be ready...")
                        not_ready_flag = False
                    time.sleep(self.NOT_READY_DELAY)
                    continue

                try:
                    item = self.bot.mouth.get(True, 0.1)
                    if isinstance(item, Exception):
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        logging.info(u"Speaker has been stopped")

    def process(self, item):
        """
        Sends one update to a business messaging space

        :param item: the update to be transmitted
        :type item: str or object

        """

        counter = self.bot.context.increment('speaker.counter')
        logging.debug(u'Speaker is working on {}'.format(counter))

        if self.bot.space is not None:
            if isinstance(item, string_types):
                self.bot.space.post_message(item)
            else:
                self.bot.space.post_message(item.text,
                                            content=item.content,
                                            file=item.file)
        else:
            logging.info(item)
