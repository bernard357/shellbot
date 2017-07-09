#!/usr/bin/env python
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
import sys
import time
import yaml
import weakref


class ShellBot(object):
    """
    Wraps underlying services in a single instance

    Shellbot allows the creation of bots with a given set of commands.
    Each bot instance is bonded to a single chat space. The chat space can be
    either created by the bot itself, or the bot can join an existing space.

    The first use case is adapted when a collaboration space is created for
    semi-automated interactions between human and machines.
    In the example below, the bot controls the entire life cycle of the chat
    space. A chat space is created when the program is launched. And it is
    deleted when the program is stopped.

    Chat space creation example::

        from shellbot import ShellBot, Context, Command
        Context.set_logger()

        # create a bot and load command
        #
        class Hello(Command):
            keyword = 'hello'
            information_message = u"Hello, World!"

        bot = ShellBot(command=Hello())

        # load configuration
        #
        bot.configure()

        # create a chat room, or connect to an existing one
        #
        bot.bond(reset=True)

        # run the bot
        #
        bot.run()

        # delete the chat room when the bot is killed
        #
        bot.dispose()

    A second interesting use case is when a bot is invited to an existing chat
    space. On such an event, a new bot instance can be created and bonded
    to the chat space.

    Chat space bonding example::

        def on_invitation(self, space_id):
            bot = ShellBot()
            bot.configure()
            bot.use_space(id=space_id)
            return bot

    A bot is an extensible set of components that share the same context,
    that is, configuration settings.

    """

    def __init__(self, engine):
        """
        Wraps underlying services in a single instance

        """
        self.engine = engine

    def bond(self, reset=False):
        """
        Bonds to a room

        :param reset: if True, delete previous room and re-create one
        :type reset: bool

        This function creates a room, or connect to an existing one.
        """
        if reset:
            self.space.delete_space(title=self.context.get('spark.room'))

        self.space.bond(
            title=self.context.get('spark.room', 'Bot under test'),
            ex_team=self.context.get('spark.team'),
            moderators=self.context.get('spark.moderators', []),
            participants=self.context.get('spark.participants', []),
        )

        self.store.bond(id=self.space.id)

        self.dispatch('bond')

    def add_moderators(self, *args, **kwargs):
        """
        Adds moderators to the room

        This function is a proxy for the underlying space.
        """
        if self.space:
            self.space.add_moderators(*args, **kwargs)

    def add_participants(self, *args, **kwargs):
        """
        Adds participants to the room

        This function is a proxy for the underlying space.
        """
        if self.space:
            self.space.add_participants(*args, **kwargs)

    def add_participant(self, *args, **kwargs):
        """
        Adds one participant to the room

        This function is a proxy for the underlying space.
        """
        if self.space:
            self.space.add_participant(*args, **kwargs)

    def remove_participants(self, *args, **kwargs):
        """
        Removes participants to the room

        This function is a proxy for the underlying space.
        """
        if self.space:
            self.space.remove_participants(*args, **kwargs)

    def remove_participant(self, *args, **kwargs):
        """
        Removes one participant from the room

        This function is a proxy for the underlying space.
        """
        if self.space:
            self.space.remove_participant(*args, **kwargs)

    def dispose(self, *args, **kwargs):
        """
        Disposes all resources

        """
        self.dispatch('dispose')
        self.space.dispose(*args, **kwargs)

    def say(self, text, content=None, file=None):
        """
        Sends a message to the chat space

        :param text: Plain text message
        :type text: str or None

        :param content: Rich content such as Markdown or HTML
        :type content: str or None

        :param file: path or URL to a file to attach
        :type file: str or None

        """
        if text in (None, ''):
            return

        logging.info(u"Bot says: {}".format(text))

        if self.mouth:
            logging.debug(u"- pushing message to mouth queue")
            self.mouth.put(Vibes(text, content, file))

        else:
            logging.debug(u"- calling speaker directly")
            self.speaker.process(Vibes(text, content, file))

    def remember(self, key, value):
        """
        Remembers a value

        :param key: name of the value
        :type key: str

        :param value: new value
        :type value: any serializable type is accepted

        This functions stores or updates a value in the back-end storage
        system.

        Example::

            bot.remember('parameter_123', 'George')

        """
        self.store.remember(key, value)

    def recall(self, key, default=None):
        """
        Recalls a value

        :param key: name of the value
        :type key: str

        :param default: default value
        :type default: any serializable type is accepted

        :return: the actual value, or the default value, or None

        Example::

            value = bot.recall('parameter_123')

        """
        return self.store.recall(key, default)

    def forget(self, key=None):
        """
        Forgets a value or all values

        :param key: name of the value to forget, or None
        :type key: str

        To clear only one value, provides the name of it.
        For example::

            bot.forget('parameter_123')

        To clear all values in the store, just call the function
        without a value.
        For example::

            bot.forget()

        """
        self.store.forget(key)

    def append(self, key, item):
        """
        Appends an item to a list

        :param key: name of the list
        :type key: str

        :param item: a new item to append
        :type item: any serializable type is accepted

        Example::

            >>>bot.append('names', 'Alice')
            >>>bot.append('names', 'Bob')
            >>>bot.recall('names')
            ['Alice', 'Bob']

        """
        self.store.append(key, item)

    def update(self, key, label, item):
        """
        Updates a dict

        :param key: name of the dict
        :type key: str

        :param label: named entry in the dict
        :type label: str

        :param item: new value of this entry
        :type item: any serializable type is accepted

        Example::

            >>>bot.update('input', 'PO Number', '1234A')
            >>>bot.recall('input')
            {'PO Number': '1234A'}

        """
        self.store.update(key, label, item)
