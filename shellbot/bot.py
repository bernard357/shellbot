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

            space.connect()

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

            space.post_message(id, 'Hello, World!')

    5. The interface allows for the addition or removal of channel
       participants::

            space.add_participants(id, persons)
            space.add_participant(id, person, is_moderator)
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
        Gets title of the related chat channel

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

    def bond(self):
        """
        Bonds to a channel

        This function is called either after the creation of a new channel,
        or when the bot has been invited to an existing channel. In such
        situations the banner should be displayed as well.

        There are also situations where the engine has been completely
        restarted. The bot bonds to a channel where it has been before.
        In that case the banner should be avoided.
        """
        assert self.is_ready

        self.store.bond(id=self.id)

        self.subscriber = self.engine.bus.subscribe('topic')
        self.publisher = self.engine.publisher
        self.publisher.put('topic', 'bot.bond()')

        self.on_bond()

        self.engine.dispatch('bond', bot=self)

        if self.machine:
            self.machine.restart(defer=2.0)

    def on_bond(self):
        """
        Adds processing to channel bonding

        This function should be changed in sub-class, where necessary.

        Example::

            def on_bond(self):
                do_something_important_on_bond()

        """
        pass

    def on_enter(self):
        """
        Enters a channel
        """
        self.say_banner()

        if self.machine:
            self.machine.restart(defer=2.0)  # no effect if machine is running

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
            self.on_exit()
            self.engine.dispatch('dispose', bot=self)
            time.sleep(2)
            self.space.delete(id=self.id, **kwargs)
            self.reset()

    def on_exit(self):
        """
        Exits a channel
        """
        text = self.engine.get('bot.on_exit', u"Bot is leaving this channel")
        self.say(text)

    def add_participants(self, persons=[]):
        """
        Adds multiple participants

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        if self.id:
            self.space.add_participants(id=self.id, persons=persons)

    def add_participant(self, person, is_moderator=False):
        """
        Adds one participant

        :param person: e-mail addresses of person to add
        :type person: str

        The underlying platform may, or not, take the optional
        parameter ``is_moderator`` into account. The default bahaviour is to
        discard it, as if the parameter had the value ``False``.

        """
        assert person not in (None, '')
        assert is_moderator in (True, False)
        if self.id:
            self.space.add_participant(id=self.id,
                                       person=person,
                                       is_moderator=is_moderator)

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
        assert person not in (None, '')
        if self.id:
            self.space.remove_participant(id=self.id, person=person)

    def say(self, text=None, content=None, file=None, person=None):
        """
        Sends a message to the chat space

        :param text: Plain text message
        :type text: str or None

        :param content: Rich content such as Markdown or HTML
        :type content: str or None

        :param file: path or URL to a file to attach
        :type file: str or None

        :param person: for direct message to someone
        :type person: str

        """
        if text:
            line = text[:50] + (text[50:] and '..')
        elif content:
            line = content[:50] + (content[50:] and '..')
        else:
            return

        logging.info(u"Bot says: {}".format(line))

        vibes = Vibes(text=text,
                      content=content,
                      file=file,
                      channel_id=None if person else self.id,
                      person=person)

        if not self.is_ready:
            logging.debug(u"- not ready to speak")

        elif self.engine.mouth:
            logging.debug(u"- pushing message to mouth queue")
            self.engine.mouth.put(vibes)

        else:
            logging.debug(u"- calling speaker directly")
            self.engine.speaker.process(vibes)

    def say_banner(self):
        """
        Sends banner to the channel

        This function uses following settings from the context:

        - ``bot.banner.text`` or ``bot.on_enter`` - a textual message

        - ``bot.banner.content`` - some rich content, e.g., Markdown or HTML

        - ``bot.banner.file`` - a document to be uploaded

        The quickest setup is to change ``bot.on_enter`` in settings, or the
        environment variable ``$BOT_ON_ENTER``.

        Example::

            os.environ['BOT_ON_ENTER'] = 'You can now chat with Batman'
            engine.configure()

        Then there are situtations where you want a lot more flexibility, and
        rely on a smart banner. For example you could do the following::

            settings = {
                'bot': {
                    'banner': {
                        'text': u"Type '@{} help' for more information",
                        'content': u"Type ``@{} help`` for more information",
                        'file': "http://on.line.doc/guide.pdf"
                    }
                }
            }

            engine.configure(settings)

        When bonding to a channel, the bot will send an update similar to the
        following one, with a nice looking message and image::

            Type '@Shelly help' for more information

        Default settings for the banner rely on the environment, so it is
        easy to inject strings from the outside. Use following variables:

        - ``$BOT_BANNER_TEXT`` or ``$BOT.ON_ENTER`` - the textual message

        - ``$BOT_BANNER_CONTENT`` - some rich content, e.g., Markdown or HTML

        - ``$BOT_BANNER_FILE`` - a document to be uploaded


        """
        text = self.engine.get('bot.banner.text')

        if not text:
            text = self.engine.get('bot.on_enter')

        if text:
            text = text.format(self.engine.name)

        content = self.engine.get('bot.banner.content')
        if content:
            content = content.format(self.engine.name)

        file = self.engine.get('bot.banner.file')

        self.say(text=text, content=content, file=file)

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
