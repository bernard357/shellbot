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
import zmq


class Bus(object):
    """
    Represents an information bus between publishers and subscribers

    In the context of shellbot, topics are channel identifiers, and messages
    are python objects serializable with json.

    A first pattern is the synchronization of direct channels from the group
    channel:

    - every direct channel is a subscriber, and filters messages sent to their
      own channel identifier

    - group channel is a publisher, and broadcast instructions to the list
      of direct channel identifiers it knows about


    A second pattern is the observation by a group channel of what is
    happening in related direct channels:

    - every direct channel is a publisher, and the topic used is their own
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
        self.zmq_context = zmq.Context()

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

    def subscribe(self, topics):
        """
        Subcribes to some topics

        :param topics: one or multiple topics
        :type topics: str or list of str

        :return: Subscriber

        Example::

            # subscribe from all direct channels related to this group channel
            subscriber = bus.subscribe(bot.direct_channels)

        """
        socket = self.zmq_context.socket(zmq.SUB)
        address = self.context.get('bus.address', self.DEFAULT_ADDRESS)
        logging.debug(u"Subscribing at {}".format(address))
        socket.connect(address)

        assert topics not in (None, '', [], ())
        if isinstance(topics, string_types):
            topics = [topics]

        for topic in topics:
            logging.debug(u"- {}".format(topic))
            socket.setsockopt(zmq.SUBSCRIBE, topic)

        return Subscriber(socket=socket)

    def publish(self):
        """
        Publishes messages

        :return: Publisher

        Example::

            # get a publisher for subsequent broadcasts
            publisher = bus.publish()

        """
        socket = self.zmq_context.socket(zmq.PUB)
        address = self.context.get('bus.address', self.DEFAULT_ADDRESS)
        logging.debug(u"Publishing at {}".format(address))
        socket.bind(address)
        return Publisher(socket=socket)


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
    def __init__(self, socket):
        """
        Subscribes to asynchronous messages

        :param socket: a ZeroMQ socket

        """
        self.socket = socket

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
        In other terms, the topic used for the communication is lost
        in translation. Therefore the need to put within messages all
        information that may be relevant for the receiver.
        """
        try:
            flags = zmq.NOBLOCK if not block else 0
            snippet = self.socket.recv(flags=flags)
            (topic, text) = snippet.split(' ', 1)
            return json.loads(text)
        except zmq.error.Again:
            return None


class Publisher(object):
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
    def __init__(self, socket):
        """
        Publishes asynchronous messages

        :param socket: a ZeroMQ socket

        """
        self.socket = socket

    def put(self, topics, message):
        """
        Broadcasts a message

        :param topics: one or multiple topics
        :type topics: str or list of str

        :param message: the message to send
        :type message: dict or other json-serializable object

        Example::

            message = { ... }
            publisher.put(bot.id, message)

        """
        assert topics not in (None, '', [], ())
        if isinstance(topics, string_types):
            topics = [topics]

        assert message not in (None, '')
        text = json.dumps(message)
        for topic in topics:
            self.socket.send(topic + ' ' + text)  # no multi-part because of non-blocking recv()
