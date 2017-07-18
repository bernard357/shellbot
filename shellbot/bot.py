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

from .speaker import Vibes


class ShellBot(object):
    """
    Manages interactions with one space, one store, one state machine

    A bot consists of multiple components devoted to one chat space:
    - a space
    - a store
    - a state machine

    It is designated by a unique id, that is also the unique id of the space
    itself.

    A bot relies on an underlying engine instance for actual access
    to the infrastructure, including configuration settings.
    """

    def __init__(self,
                 engine,
                 space_id=None,
                 space=None,
                 store=None,
                 fan=None,
                 machine=None):
        """
        Manages interactions with one space, one store, one state machine

        :param engine: Engine instance for acces of the infrastructure
        :type engine: Engine

        :param space_id: Unique id of the related chat space
        :type space_id: str

        :param space: Chat space related to this bot
        :type space: Space

        :param store: Data store related to this bot
        :type store: Store

        :param fan: For asynchronous handling of user input
        :type fan: Queue

        :param machine: State machine related to this bot
        :type machine: Machine

        """
        self.engine = engine

        assert space_id is None or space is None  # use only one
        if space_id:
            self.space = self.engine.build_space(space_id)
        elif space:
            self.space = space
        else:
            self.space = engine.space

        if store:
            self.store = store
        else:
            self.store = self.engine.build_store(space_id)

        self.fan = fan if fan else Queue()

        self.machine = machine

        self.on_init()

    def on_init(self):
        """
        Adds to bot initialization

        It can be overlaid in subclass, where needed
        """
        pass

    @property
    def space_id(self):
        """
        Gets unique id of the related chat space

        :return: the id of the underlying space, or None
        """
        if self.space:
            return self.space.id

        return None

    def bond(self, reset=False):
        """
        Bonds to a room

        :param reset: if True, delete previous room and re-create one
        :type reset: bool

        This function creates a room, or connect to an existing one.
        """
        if reset:
            self.space.delete_space(title=self.engine.get('spark.room'))

        self.space.bond(
            title=self.engine.get('spark.room', 'Bot under test'),
            ex_team=self.engine.get('spark.team'),
            moderators=self.engine.get('spark.moderators', []),
            participants=self.engine.get('spark.participants', []),
        )

        self.store.bond(id=self.space.id)

        self.engine.dispatch('bond')

        if self.machine:
            self.machine.start()

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
        self.engine.dispatch('dispose')
        self.space.dispose(*args, **kwargs)

    def say(self, text=None, content=None, file=None):
        """
        Sends a message to the chat space

        :param text: Plain text message
        :type text: str or None

        :param content: Rich content such as Markdown or HTML
        :type content: str or None

        :param file: path or URL to a file to attach
        :type file: str or None

        """
        if text:
            line = text[:50] + (text[50:] and '..')
        elif content:
            line = content[:50] + (content[50:] and '..')
        else:
            return

        logging.info(u"Bot says: {}".format(line))

        if self.engine.mouth:
            logging.debug(u"- pushing message to mouth queue")
            self.engine.mouth.put(
                Vibes(text, content, file, self.space_id))

        else:
            logging.debug(u"- calling speaker directly")
            self.engine.speaker.process(
                Vibes(text, content, file, self.space_id))

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

            bot.remember('variable_123', 'George')

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

            value = bot.recall('variable_123')

        """
        return self.store.recall(key, default)

    def forget(self, key=None):
        """
        Forgets a value or all values

        :param key: name of the value to forget, or None
        :type key: str

        To clear only one value, provides the name of it.
        For example::

            bot.forget('variable_123')

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
            >>>bot.update('input', 'description', 'some description')
            >>>bot.recall('input')
            {'PO Number': '1234A',
             'description': 'some description'}

        """
        self.store.update(key, label, item)
