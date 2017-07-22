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

    A bot consists of multiple components devoted to one chat channel:
    - a space
    - a store
    - a state machine
    - ... other optional components that may prove useful

    It is designated by a unique id, that is also the unique id of the channel
    itself.

    A bot relies on an underlying engine instance for actual access
    to the infrastructure, including configuration settings.

    The life cycle of a bot can be described as follows::

    1. A bot is commonly created from the engine, or directly::

            bot = ShellBot(engine, channel_id='123')

    2. The space is connected to some back-end API::

            >>>space.connect()

    3. Multiple channels can be handled by a single space::

            channel = space.create(title)

            channel = space.get_by_title(title)
            channel = space.get_by_id(id)

            channel.title = 'A new title'
            space.update(channel)

            space.delete(id)

       Channels feature common attributes, yet can be extended to
       convey specificities of some platforms.

    4. Messages can be posted::

           >>>space.post_message(id, 'Hello, World!')

    5. The interface distinguishes between space participants and
       moderators::

            space.add_participants(id, persons)
            space.add_participant(id, person)
            space.add_moderators(id, persons)
            space.add_moderator(id, person)
            space.remove_participants(id, persons)
            space.remove_participant(id, person)


    """

    def __init__(self,
                 engine,
                 channel_id=None,
                 space=None,
                 store=None,
                 fan=None,
                 machine=None):
        """
        Manages interactions with one space, one store, one state machine

        :param engine: Engine instance for acces of the infrastructure
        :type engine: Engine

        :param channel_id: Unique id of the related chat space
        :type channel_id: str

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

        if space:
            self.space = space
        else:
            self.space = engine.space

        if channel_id:
            self.channel = self.space.get_by_id(channel_id)
        else:
            self.channel = None

        if store:
            self.store = store
        else:
            self.store = self.engine.build_store(channel_id)

        self.fan = fan if fan else Queue()

        self.machine = machine

        self.on_init()

    def on_init(self):
        """
        Adds to bot initialization

        It can be overlaid in subclass, where needed
        """
        pass

    def bond(self,
             title=None,
             reset=False,
             moderators=None,
             participants=None,
             **kwargs):
        """
        Bonds to a channel

        :param title: title of the target channel
        :type: title: str

        :param reset: if True, delete previous room and re-create one
        :type reset: bool

        :param moderators: the list of initial moderators (optional)
        :type moderators: list of str

        :param participants: the list of initial participants (optional)
        :type participants: list of str

        This function creates a channel, or connect to an existing one.
        If no title is provided, then the generic title configured for the
        underlying space is used instead.
        """
        if title in (None, ''):
            title=self.space.configured_title()

        logging.debug(u"Bonding to channel '{}'".format(title))

        self.channel = self.space.get_by_title(title=title)
        if self.channel and not reset:
            logging.debug(u"- found existing channel")

        else:
            if self.channel and reset:
                logging.debug(u"- deleting existing channel")
                self.space.delete(id=self.channel.id)

            logging.debug(u"- creating channel '{}''".format(title))
            self.channel = self.space.create(title=title, **kwargs)

            bot = self.engine.context.get('bot.email')
            logging.debug(u"- adding bot {}".format(bot))
            self.add_participant(bot)

            if not moderators:
                moderators = self.space.get('moderators', [])
            self.add_moderators(persons=moderators)

            if not participants:
                participants = self.space.get('participants', [])
            self.add_participants(persons=participants)

        self.store.bond(id=self.id)

        self.engine.dispatch('bond')

        self.on_bond()

    def on_bond(self):
        """
        Adds processing to space bond

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_bond(self):
                self.say('I am alive!')

        """
        pass

    @property
    def is_ready(self):
        """
        Checks if this bot is ready for interactions

        :return: True or False
        """
        if self.id is None:
            return False

        return True

    @property
    def id(self):
        """
        Gets unique id of the related chat channel

        :return: the id of the underlying channel, or None
        """
        if self.channel:
            return self.channel.id

        return None

    @property
    def title(self):
        """
        Gets titleof the related chat channel

        :return: the title of the underlying channel, or None
        """
        if self.channel:
            return self.channel.title

        return None

    def reset(self):
        """
        Resets a space

        After a call to this function, ``bond()`` has to be invoked to
        return to normal mode of operation.
        """
        if self.channel:
            self.channel = None

        self.on_reset()

    def on_reset(self):
        """
        Adds processing to space reset

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_reset(self):
                self._last_message_id = 0

        """
        pass

    def dispose(self, **kwargs):
        """
        Disposes all resources

        This function deletes the underlying channel in the cloud and resets
        this instance. It is useful to restart a clean environment.

        >>>bot.bond(title="Working Space")
        ...
        >>>bot.dispose()

        After a call to this function, ``bond()`` has to be invoked to
        return to normal mode of operation.
        """

        if self.id:
            self.engine.dispatch('dispose', bot=self)
            self.space.delete(id=self.id, **kwargs)
            self.reset()

    def add_moderators(self, persons=[]):
        """
        Adds multiple moderators

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        if self.id:
            self.space.add_moderators(id=self.id, persons=persons)

    def add_moderator(self, person):
        """
        Adds one moderator

        :param person: e-mail addresses of person to add
        :type person: str

        """
        if self.id:
            self.space.add_moderator(id=self.id, person=person)

    def add_participants(self, persons=[]):
        """
        Adds multiple participants

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        if self.id:
            self.space.add_participants(id=self.id, persons=persons)

    def add_participant(self, person):
        """
        Adds one participant

        :param person: e-mail addresses of person to add
        :type person: str

        """
        if self.id:
            self.space.add_participant(id=self.id, person=person)

    def remove_participants(self, persons=[]):
        """
        Removes multiple participants

        :param persons: e-mail addresses of persons to remove
        :type persons: list of str

        """
        if self.id:
            self.space.remove_participants(id=self.id, persons=persons)

    def remove_participant(self, person):
        """
        Removes one participant

        :param person: e-mail addresses of person to add
        :type person: str

        """
        if self.id:
            self.space.remove_participant(id=self.id, person=person)

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

        if not self.is_ready:
            logging.debug(u"- not ready to speak")

        elif self.engine.mouth:
            logging.debug(u"- pushing message to mouth queue")
            self.engine.mouth.put(
                Vibes(text, content, file, self.id))

        else:
            logging.debug(u"- calling speaker directly")
            self.engine.speaker.process(
                Vibes(text, content, file, self.id))

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
