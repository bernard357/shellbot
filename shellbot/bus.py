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

from builtins import str
import json
import logging
from multiprocessing import Process, Queue
from six import string_types
import time
import zmq


class Bus(object):
    """
    Represents an information bus between publishers and subscribers

    In the context of shellbot, channels are channel identifiers, and messages
    are python objects serializable with json.

    A first pattern is the synchronization of direct channels from the group
    channel:

    - every direct channel is a subscriber, and filters messages sent to their
      own channel identifier

    - group channel is a publisher, and broadcast instructions to the list
      of direct channel identifiers it knows about


    A second pattern is the observation by a group channel of what is
    happening in related direct channels:

    - every direct channel is a publisher, and the channel used is their own
      channel identifier

    - group channel is a subscriber, and observed messages received from all
      direct channels it knows about


    For example, a distributed voting system can be built by combining
    the two patterns. The vote itself can be triggered simultaneously to
    direct channels on due time, so that every participants are involved
    more or less at the same time. And data that is collected in direct
    channels can ce centralised back to the group channel where results
    are communicated.

    """

#    DEFAULT_ADDRESS = 'ipc://shellbot'
    DEFAULT_ADDRESS = 'tcp://127.0.0.1:5555'

    def __init__(self, context):
        """
        Represents an information bus between publishers and subscribers

        :param context: general settings
        :type context: Context

        """
        self.context = context

    def check(self):
        """
        Checks configuration settings

        This function reads key ``bus`` and below, and update
        the context accordingly. It handles following parameters:

        * ``bus.address`` - focal point of bus exchanges on the network.
          The default value is ``tcp://*:5555`` which means 'use TCP port 5555
          on local machine'.

        """
        self.context.check('bus.address', self.DEFAULT_ADDRESS)

    def subscribe(self, channels):
        """
        Subcribes to some channels

        :param channels: one or multiple channels
        :type channels: str or list of str

        :return: Subscriber

        Example::

            # subscribe from all direct channels related to this group channel
            subscriber = bus.subscribe(bot.direct_channels)

            ...

            # get next message from these channels
            message = subscriber.get()

        """
        return Subscriber(context=self.context, channels=channels)

    def publish(self):
        """
        Publishes messages

        :return: Publisher

        Example::

            # get a publisher for subsequent broadcasts
            publisher = bus.publish()

            # start the publishing process
            publisher.start()

            ...

            # broadcast information_message
            publisher.put(channel, message)

        """
        return Publisher(context=self.context)


class Subscriber(object):
    """
    Subscribes to asynchronous messages

    For example, from a group channel, you may subscribe from
    direct channels of all participants::

        # subscribe from all direct channels related to this group channel
        subscriber = bus.subscribe(bot.direct_channels)

        # get messages from direct channels
        while True:
            message = subscriber.get()
            ...

    From within a direct channel, you may receive instructions sent
    by the group channel::

        # subscribe for messages sent to me
        subscriber = bus.subscribe(bot.id)

        # get and process instructions one at a time
        while True:
            instruction = subscriber.get()
            ...

    """
    def __init__(self, context, channels):
        """
        Subscribes to asynchronous messages

        :param context: general settings
        :type context: Context

        :param channels: one or multiple channels
        :type channels: str or list of str

        """
        self.context = context
        address=self.context.get('bus.address')
        logging.debug(u"Subscribing at {}".format(address))

        assert channels not in (None, [], ())
        if isinstance(channels, string_types):
            channels = [channels]
        self.channels = channels

        for channel in self.channels:
            if channel:
                logging.debug(u"- {}".format(channel))
            else:
                logging.debug(u"- {}".format('<all channels>'))

        self.socket = None  # defer binding to first get()

    def get(self, block=False):
        """
        Gets next message

        :return: dict or other serializable message or None

        This function returns next message that has been made available,
        or None if no message has arrived yet.

        Example::

            message = subscriber.get()  # immedaite return
            if message:
                ...

        Change the parameter ``block`` if you prefer to wait until next
        message arrives.

        Example::

            message = subscriber.get(block=True)  # wait until available

        Note that this function does not preserve the enveloppe of the message.
        In other terms, the channel used for the communication is lost
        in translation. Therefore the need to put within messages all
        information that may be relevant for the receiver.
        """
        if not self.socket:
            zmq_context = zmq.Context.instance()
            self.socket = zmq_context.socket(zmq.SUB)
            self.socket.linger = 0
            address=self.context.get('bus.address')
            self.socket.connect(address)

            for channel in self.channels:
                self.socket.setsockopt_string(zmq.SUBSCRIBE, str(channel))

        try:
            flags = zmq.NOBLOCK if not block else 0
            snippet = self.socket.recv(flags=flags)
            (channel, text) = snippet.split(' ', 1)
            return json.loads(text)
        except zmq.error.Again:
            return None


class Publisher(Process):
    """
    Publishes asynchronous messages

    For example, from a group channel, you may send instructions to every
    direct channels::

        # get a publisher
        publisher = bus.publish()

        # send instruction to direct channels
        publisher.put(bot.direct_channels, instruction)

    From within a direct channel, you may reflect your state to observers::

        # get a publisher
        publish = bus.publish()

        # share new state
        publisher.put(bot.id, bit_of_information_here)

    """

    DEFER_DURATION = 0.3  # allow subscribers to connect
    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, context):
        """
        Publishes asynchronous messages

        :param context: general settings
        :type context: Context

        """
        Process.__init__(self)
        self.daemon = True

        self.context = context

        self.fan = Queue()

        self.socket = None  # allow socket injection for tests

    def run(self):
        """
        Continuously broadcasts messages

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            publisher = Publisher(address)
            process = publisher.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Alternatively, the loop is also broken when a poison pill is pushed
        to the queue. For example::

            publisher.fan.put(None)

        """
        address=self.context.get('bus.address')

        if not self.socket:
            zmq_context = zmq.Context.instance()
            self.socket = zmq_context.socket(zmq.PUB)
            self.socket.linger = 0
            self.socket.bind(address)

        time.sleep(self.DEFER_DURATION)  # allow subscribers to connect

        logging.info(u"Starting publisher")
        logging.debug(u"- publishing at {}".format(address))

        try:
            self.context.set('publisher.counter', 0)
            while self.context.get('general.switch', 'on') == 'on':

                if self.fan.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.fan.get_nowait()
                    if item is None:
                        break

                    self.context.increment('publisher.counter')
                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        self.socket.close()
        self.socket = None

        logging.info("Publisher has been stopped")

    def process(self, item):
        """
        Processes items received from the queue

        :param item: the item received
        :type item: str

        Note that the item should result from serialization
        of (channel, message) tuple done previously.
        """
        logging.debug(u"Publishing {}".format(item))
        self.socket.send_string(item)

    def put(self, channels, message):
        """
        Broadcasts a message

        :param channels: one or multiple channels
        :type channels: str or list of str

        :param message: the message to send
        :type message: dict or other json-serializable object

        Example::

            message = { ... }
            publisher.put(bot.id, message)

        This function actually put the message in a global queue that is
        handled asynchronously. Therefore, when the function returns there is
        no guarantee that message has been transmitted nor received.
        """
        assert channels not in (None, '', [], ())
        if isinstance(channels, string_types):
            channels = [channels]

        assert message not in (None, '')
        text = json.dumps(message)
        for channel in channels:
            item = channel + ' ' + text
            logging.debug(u"Queuing {}".format(item))
            self.fan.put(item)
