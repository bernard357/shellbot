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
from six import string_types
import time
import yaml

from .events import Event, Message, Attachment, Join, Leave


class Listener(object):
    """
    Handles messages received from chat space
    """

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, bot=None, filter=None):
        """
        Handles events received from chat space

        :param bot: the overarching bot
        :type bot: ShellBot

        :param filter: if provided, used to filter every event
        :type filter: callable

        If a ``filter`` is provided, then it is called for each event received.
        An event may be a Message, an Attachment, a Join or Leave notification,
        or any other Event.

        Example::

            def filter(event):

                # duplicate input stream
                my_queue.put(str(event))

                # change input stream
                event.text = event.text.title()

                return event

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
        Processes items received from the chat space

        :param item: the item received
        :type item: dict or json-encoded string

        This function dispatches items based on their type. The type is
        a key of the provided dict.

        Following types are handled:

        * ``message`` -- This is a textual message, maybe with a file attached.
          The message is given to the ``on_message()`` function. If a file
          or a link is provided, the, ``on_attachment()`` function is called
          as well.

        * ``join`` -- This is when a person join a space. The function
          ``on_join()`` is called, providing details on the person who joined

        * ``leave`` -- This is when a person leaves a space. The function
          ``on_leave()`` is called with details on the leaving person.

        * on any other case, the function ``on_event()`` is
          called.
        """
        counter = self.bot.context.increment('listener.counter')
        logging.debug(u'Listener is working on {}'.format(counter))

        try:
            if isinstance(item, string_types):
                item = yaml.safe_load(item)  # better unicode than json.loads()

            assert isinstance(item, dict)  # low-level event representation

            if item['type'] == 'message':
                logging.debug(u"- dispatching a message event")
                self.on_message(Message(item))

            elif item['type'] == 'attachment':
                logging.debug(u"- dispatching an attachment event")
                self.on_attachment(Attachment(item))

            elif item['type'] == 'join':
                logging.debug(u"- dispatching a join event")
                self.on_join(Join(item))

            elif item['type'] == 'leave':
                logging.debug(u"- dispatching a leave event")
                self.on_leave(Leave(item))

            else:
                logging.debug(u"- dispatching an event")
                self.on_event(Event(item))

        except AssertionError as feedback:
            logging.debug(u"- invalid format, thrown away")
            raise ValueError(feedback)

        except Exception as feedback:
            logging.debug(u"- invalid format, thrown away")
            raise

    def on_message(self, item):
        """
        A message has been received

        :param item: the message received
        :type item: Message

        This function listens for specific commands in the coming flow.
        When a command has been identified, it is responded immediately.
        Commands that require significant processing time are pushed
        to the inbox.

        """
        assert item.type == 'message'  # sanity check

        if item.text is None:
            logging.debug(u"- no input in this item, thrown away")
            return

        if self.filter:
            item = self.filter(item)

#        print(item)

        if item.from_id == self.bot.context.get('bot.id'):
            logging.debug(u"- sent by me, thrown away")
            return

        input = item.text
        if len(input) > 0 and input[0] in ['@', '/', '!']:
            input = input[1:]

        bot = self.bot.context.get('bot.name', 'shelly')
        if input.lower().startswith(bot):
            input = input[len(bot):].strip()

        elif self.bot.context.get('bot.id') not in item.mentioned_ids:
            logging.info(u"- not for me, thrown away")
            return

        self.bot.shell.do(input)

    def on_attachment(self, item):
        """
        An attachment has been received

        :param item: the message received
        :type item: Attachment
        """
        assert item.type == 'attachment'

        if self.filter:
            item = self.filter(item)

    def on_join(self, item):
        """
        A person has joined a space

        :param item: the event received
        :type item: Join
        """
        assert item.type == 'join'

        if self.filter:
            item = self.filter(item)

    def on_leave(self, item):
        """
        A person has leaved a space

        :param item: the event received
        :type item: Leave
        """
        assert item.type == 'leave'

        if self.filter:
            item = self.filter(item)

    def on_event(self, item):
        """
        Another event has been received

        :param item: the event received
        :type item: Event or derivative
        """
        assert item.type not in ('message', 'attachment', 'join', 'leave')

        if self.filter:
            item = self.filter(item)

