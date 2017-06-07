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

    FRESH_DURATION = 0.5  # maximum amount of time for listener detection

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
          The message is given to the ``on_message()`` function.

        * ``attachment`` -- A file has been attached to the chat space. The
          ``on_attachment()`` function is invoked.

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
                logging.debug(u"- dispatching a 'message' event")
                event = Message(item)
                if self.filter:
                    event = self.filter(event)
                self.on_message(event)

            elif item['type'] == 'attachment':
                logging.debug(u"- dispatching an 'attachment' event")
                event = Attachment(item)
                if self.filter:
                    event = self.filter(event)
                self.on_attachment(event)

            elif item['type'] == 'join':
                logging.debug(u"- dispatching a 'join' event")
                event = Join(item)
                if self.filter:
                    event = self.filter(event)
                self.on_join(event)

            elif item['type'] == 'leave':
                logging.debug(u"- dispatching a 'leave' event")
                event = Leave(item)
                if self.filter:
                    event = self.filter(event)
                self.on_leave(event)

            else:
                logging.debug(u"- dispatching an inbound event")
                event = Event(item)
                if self.filter:
                    event = self.filter(event)
                self.on_inbound(event)

        except AssertionError as feedback:
            logging.debug(u"- invalid format, thrown away")
            raise ValueError(feedback)

        except Exception as feedback:
            logging.debug(u"- invalid format, thrown away")
            raise

    def on_message(self, received):
        """
        A message has been received

        :param received: the message received
        :type received: Message

        Received information is dispatched to subscribers of the event
        ``message`` at the bot level.

        When a message is directed to the bot it is submitted directly to the
        shell. This is handled as a command, that can be executed immediately,
        or pushed to the inbox and processed by the worker  when possible.

        All other input is thrown away, except if there is some
        downwards listeners. In that situation the input is pushed to a queue
        so that some process can pick it up and process it.

        The protocol for downwards listeners works like this:

        * Check the ``bot.fan`` queue frequently

        * On each check, update the string ``fan.stamp`` in the context with
          the value of ``time.time()``. This will signal that you are around.

        The value of ``fan.stamp`` is checked on every message that is not
        for the bot itself. If this is fresh enough, then data is put to the
        ``bot.fan`` queue. Else message is just thrown away.
        """
        assert received.type == 'message'  # sanity check

        self.bot.dispatch('message', received=received)

        if received.from_id == self.bot.context.get('bot.id'):
            logging.debug(u"- sent by me, thrown away")
            return

        input = received.text

        if input is None:
            logging.debug(u"- no input in this item, thrown away")
            return

        if len(input) > 0 and input[0] in ['@', '/', '!']:
            input = input[1:]

        bot = self.bot.context.get('bot.name', 'shelly')
        if input.lower().startswith(bot):
            input = input[len(bot):].strip()

        elif self.bot.context.get('bot.id') in received.mentioned_ids:
            pass # send to the shell

        else: # not explicitly intended for the bot

            elapsed = time.time() - self.bot.context.get('fan.stamp', 0)
            if elapsed < self.FRESH_DURATION:
                self.bot.fan.put(input)  # forward downstream

            logging.info(u"- not for me, thrown away")
            return

        self.bot.shell.do(input)

    def on_attachment(self, received):
        """
        An attachment has been received

        :param received: the event received
        :type received: Attachment

        Received information is dispatched to subscribers of the event
        ``attachment`` at the bot level.

        """
        assert received.type == 'attachment'

        self.bot.dispatch('attachment', received=received)

    def on_join(self, received):
        """
        A person has joined a space

        :param received: the event received
        :type received: Join

        Received information is dispatched to subscribers of the event
        ``join`` at the bot level.

        """
        assert received.type == 'join'

        self.bot.dispatch('join', received=received)

    def on_leave(self, received):
        """
        A person has leaved a space

        :param received: the event received
        :type received: Leave

        Received information is dispatched to subscribers of the event
        ``leave`` at the bot level.

        """
        assert received.type == 'leave'

        self.bot.dispatch('leave', received=received)

    def on_inbound(self, received):
        """
        Another event has been received

        :param received: the event received
        :type received: Event or derivative

        Received information is dispatched to subscribers of the event
        ``inbound`` at the bot level.

        """
        assert received.type not in ('message', 'attachment', 'join', 'leave')

        self.bot.dispatch('inbound', received=received)

