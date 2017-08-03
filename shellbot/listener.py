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
from multiprocessing import Process
import random
from six import string_types
import time
import yaml

from .events import Event, Message, Join, Leave


class Listener(Process):
    """
    Handles messages received from chat space
    """

    DEFER_DURATION = 2.0  # let SSL stabilize before pumping from the queue
    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    FRESH_DURATION = 0.5  # maximum amount of time for listener detection

    def __init__(self, engine=None, filter=None):
        """
        Handles events received from chat spaces

        :param engine: the overarching engine
        :type engine: Engine

        :param filter: if provided, used to filter every event
        :type filter: callable

        If a ``filter`` is provided, then it is called for each event received.
        An event may be a Message, a Join or Leave notification,
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
        Process.__init__(self)
        self.engine = engine
        self.filter = filter

    def run(self):
        """
        Continuously receives updates

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            listener = Listener(engine=my_engine)
            process = listener.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Alternatively, the loop is also broken when a poison pill is pushed
        to the queue. For example::

            engine.ears.put(None)

        """
        logging.info(u"Starting listener")

        time.sleep(self.DEFER_DURATION)  # let SSL stabilize first

        try:
            self.engine.set('listener.counter', 0)
            while self.engine.get('general.switch', 'on') == 'on':

                if self.engine.get('listener.lock', 'off') == 'on':
                    time.sleep(0.001)
                    continue

                if self.engine.ears.empty():
                    self.idle()
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.engine.ears.get_nowait()
                    if item is None:
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        logging.info(u"Listener has been stopped")

    def idle(self):
        """
        Finds something smart to do
        """
        if self.engine.bots_to_load:
            id = self.engine.bots_to_load.pop()
            self.engine.ears.put({'type': 'load_bot', 'id': id})

        elif not self.engine.get('vacuum.stamp'):
            self.engine.set('vacuum.stamp', time.time())

        elif time.time() - self.engine.get('vacuum.stamp') > 5.0:
            self.engine.set('vacuum.stamp', time.time())

            if self.engine.bots:
                id = random.choice(self.engine.bots.keys())
            # if id:
            #     logging.debug(u"- to vacuum: {}".format(id))

#            self.engine.vacuum.put()

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

        * ``join`` -- This is when a person or the bot joins a space.
          The function ``on_join()`` is called, providing details on the
          person or the bot who joined

        * ``leave`` -- This is when a person or the bot leaves a space.
          The function ``on_leave()`` is called with details on the
          leaving person or bot.

        * ``load_bot`` -- This is a special event to load the cache in the
          process that is running the listener. The identifier of the channel
          to load is provided as well.

        * on any other case, the function ``on_inbound()`` is
          called.
        """
        counter = self.engine.context.increment('listener.counter')
        logging.debug(u'Listener is working on {}'.format(counter))

        if isinstance(item, string_types):
            item = yaml.safe_load(item)  # better unicode than json.loads()

        assert isinstance(item, dict)  # low-level event representation

        if item['type'] == 'message':
            logging.debug(u"- processing a 'message' event")
            event = Message(item)
            if self.filter:
                event = self.filter(event)
            self.on_message(event)

        elif item['type'] == 'join':
            logging.debug(u"- processing a 'join' event")
            event = Join(item)
            if self.filter:
                event = self.filter(event)
            self.on_join(event)

        elif item['type'] == 'leave':
            logging.debug(u"- processing a 'leave' event")
            event = Leave(item)
            if self.filter:
                event = self.filter(event)
            self.on_leave(event)

        elif item['type'] == 'load_bot':
            logging.debug(u"- processing a 'load_bot' event")
            bot = self.engine.get_bot(channel_id=item['id'])

        else:
            logging.debug(u"- processing an inbound event")
            event = Event(item)
            if self.filter:
                event = self.filter(event)
            self.on_inbound(event)

    def on_message(self, received):
        """
        A message has been received

        :param received: the message received
        :type received: Message

        Received information is transmitted to registered callbacks on the
        ``message`` event at the engine level.

        When a message is directed to the bot it is submitted directly to the
        shell. This is handled as a command, that can be executed immediately,
        or pushed to the inbox and processed by the worker  when possible.

        All other input is thrown away, except if there is some
        downwards listeners. In that situation the input is pushed to a queue
        so that some process can pick it up and process it.

        The protocol for downwards listeners works like this:

        * Check the ``bot.fan`` queue frequently

        * On each check, update the string ``fan.<channel_id>`` in the context
          with the value of ``time.time()``. This will say that you are around.

        The value of ``fan.<channel_id>`` is checked on every message that is not
        for the bot itself. If this is fresh enough, then data is put to the
        ``bot.fan`` queue. Else message is just thrown away.
        """
        assert received.type == 'message'  # sanity check

        self.engine.dispatch('message', received=received)

        bot = self.engine.get_bot(received.channel_id)

        if received.from_id == self.engine.get('bot.id'):
            logging.debug(u"- sent by me, thrown away")
            return

        input = received.text

        if input is None:
            logging.debug(u"- no input in this item, thrown away")
            return

        if len(input) > 0 and input[0] in ['@', '/', '!']:
            input = input[1:]

        label = 'fan.' + received.channel_id
        logging.debug(u"- sensing fan listener on '{}'".format(label))

        elapsed = time.time() - self.engine.get(label, 0)
        if elapsed < self.FRESH_DURATION:
            logging.debug(u"- putting input to fan queue")
            bot.fan.put(input)  # forward downstream
            return

        name = self.engine.get('bot.name', 'shelly')
        if input.startswith(name):
            logging.debug(u"- bot name in command")
            input = input[len(name):].strip()

        elif received.is_direct:
            logging.debug(u"- direct message")

        elif self.engine.get('bot.id') in received.mentioned_ids:
            logging.debug(u"- bot mentioned in command")

        else:
            logging.info(u"- not for me, thrown away")
            return

        logging.debug(u"- submitting command to the shell")
        self.engine.shell.do(input, received=received)

    def on_join(self, received):
        """
        A person, or the bot, has joined a space

        :param received: the event received
        :type received: Join

        Received information is transmitted to registered callbacks on the
        ``join`` at the engine level.

        In the special case where the bot itself is joining a channel by
        invitation, then the event ``enter`` is dispatched instead.

        """
        assert received.type == 'join'

        if received.actor_id == self.engine.get('bot.id'):
            self.engine.dispatch('enter', received=received)
            bot = self.engine.get_bot(received.channel_id)
            self.engine.on_enter(received)
        else:
            bot = self.engine.get_bot(received.channel_id)
            self.engine.dispatch('join', received=received)

    def on_leave(self, received):
        """
        A person, or the bot, has left a space

        :param received: the event received
        :type received: Leave

        Received information is transmitted to registered callbacks on the
        ``leave`` at the engine level.

        In the special case where the bot itself has been kicked off
        from a channel, then the event ``exit`` is dispatched instead.

        """
        assert received.type == 'leave'

        if received.actor_id == self.engine.get('bot.id'):
            self.engine.dispatch('exit', received=received)
            self.engine.on_exit(received)
        else:
            self.engine.dispatch('leave', received=received)

    def on_inbound(self, received):
        """
        Another event has been received

        :param received: the event received
        :type received: Event or derivative

        Received information is transmitted to registered callbacks on the
        ``inbound`` at the engine level.

        """
        assert received.type not in ('message', 'join', 'leave')

        self.engine.dispatch('inbound', received=received)
