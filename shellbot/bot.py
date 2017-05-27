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
import sys
import time
import yaml
import weakref

from .context import Context
from .shell import Shell
from .listener import Listener
from .server import Server
from .spaces import SpaceFactory
from .speaker import Speaker
from .stores import StoreFactory
from .worker import Worker
from .routes.wrap import Wrap


class ShellBot(object):
    """
    Wraps underlying services in a single instance

    Example::

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

        # create a chat room
        #
        bot.bond(reset=True)

        # run the bot
        #
        bot.run()

        # delete the chat room when the bot is killed
        #
        bot.dispose()

    """

    DEFAULT_SETTINGS = {

        'bot': {
            'on_start': '$BOT_ON_START',
            'on_stop': '$BOT_ON_STOP',
        },

        'spark': {
            'room': '$CHAT_ROOM_TITLE',
            'moderators': '$CHAT_ROOM_MODERATORS',
            'token': '$CHAT_TOKEN',
        },

        'server': {
            'url': '$SERVER_URL',
            'hook': '/hook',
            'binding': '0.0.0.0',
            'port': 8080,
        },

    }

    def __init__(self,
                 context=None,
                 command=None,
                 commands=None,
                 mouth=None,
                 inbox=None,
                 ears=None,
                 fan=None,
                 configure=False,
                 settings={},
                 space=None,
                 type=None,
                 server=None,
                 store=None):
        """
        Wraps underlying services in a single instance

        """

        self.context = context if context else Context()

        self.mouth = mouth
        self.inbox = inbox
        self.ears = ears
        self.fan = fan

        assert space is None or type is None  # use only one
        if type:
            space = SpaceFactory.get(type=type)
        self.space = space
        if self.space:
            self.space.bot = self

        self.server = server
        self.store = store

        self.shell = Shell(bot=self)

        self.speaker = Speaker(bot=self)
        self.worker = Worker(bot=self)
        self.listener = Listener(bot=self)

        if configure or settings:
            self.configure(settings)

        if commands:
            self.load_commands(commands)

        if command:
            self.load_command(command)

        self.registered = {
            'bond': [],     # connected to a space
            'dispose': [],  # space will be destroyed
            'start': [],    # starting bot services
            'stop': [],     # stopping bot services
        }

    def configure_from_path(self, path="settings.yaml"):
        """
        Reads configuration information

        :param path: path to the configuration file
        :type path: str

        The function loads configuration from the file and from the
        environment. Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        logging.info(u"Loading configuration")
        logging.info(u"- from '{}'".format(path))
        with open(path, 'r') as stream:
            self.configure_from_file(stream)

    def configure_from_file(self, stream):
        """
        Reads configuration information

        :param stream: the handle that contains configuration information
        :type stream: file

        The function loads configuration from the file and from the
        environment. Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        try:
            settings = yaml.load(stream)
        except Exception as feedback:
            logging.error(feedback)
            sys.exit(1)

        self.configure(settings)

    def configure(self, settings=None):
        """
        Checks settings

        :param settings: configuration information
        :type settings: dict

        If no settings is provided, then ``self.DEFAULT_SETTINGS`` is used
        instead.
        """

        if settings is None:
            settings = self.DEFAULT_SETTINGS

        self.configure_from_dict(settings)

        if self.fan is None:
            self.fan = Queue()

        self.shell.configure()

        if self.space is None:
            self.space = SpaceFactory.build(self)
        else:
            self.space.configure()

        self.space.connect()

        if self.store is None:
            self.store = StoreFactory.build(self)
        else:
            self.store.configure()

        if (self.server is None
            and self.context.get('server.binding') is not None):

            logging.debug(u"Adding web server")
            self.server = Server(context=self.context, check=True)

    def configure_from_dict(self, settings):
        """
        Changes settings of the bot

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``bot`` and below, and update
        the context accordingly.
        It also reads hook parameters under ``server``::

            shell.configure_fom_dict({

                'bot': {
                    'on_start': 'You can now chat with Batman',
                    'on_stop': 'Batman is now quitting the room, bye',
                },

                'server': {
                    'url': 'http://d9b62df9.ngrok.io',
                    'hook': '/hook',
                },

            })

        This can also be written in a more compact form::

            shell.configure({'bot.on_banner': 'Hello, I am here to help'})

        """

        self.context.apply(settings)
        self.context.check('bot.on_start', '', filter=True)
        self.context.check('bot.on_stop', '', filter=True)

    def get(self, key, default=None):
        """
        Retrieves the value of one configuration key

        :param key: name of the value
        :type key: str

        :param default: default value
        :type default: any serializable type is accepted

        :return: the actual value, or the default value, or None

        Example::

            message = bot.get('bot.on_start')

        This function is safe on multiprocessing and multithreading.

        """
        return self.context.get(key, default)

    def register(self, event, instance):
        """
        Registers an object to process an event

        :param event: label, such as 'start' or 'bond'
        :type event: str

        :param instance: an object that will handle the event
        :type instance: object

        This function is used to propagate bot events to any module
        that may need it.

        Example::

            def on_init(self):
                self.bot.register('bond', self)  # call self.on_bond()
                self.bot.register('dispose', self) # call self.on_dispose()

        Following events can be registered:

        - 'bond' - when the bot has connected to a chat space

        - 'dispose' - when resources, including chat space, will be destroyed

        - 'start' - when bot services are started

        - 'stop' - when bot services are stopped

        On each event, the bot will look for a related member function
        in the target instance and call it. For example for the event
        'start' it will look for the member function 'on_start', etc.

        Registration uses weakref so that it affords the unattended deletion
        of registered objects.
        """
        assert event in self.registered.keys()  #  avoid unknown event type

        name = 'on_' + event
        callback = getattr(instance, name)
        assert callable(callback) # ensure the event is supported

        handle = weakref.proxy(instance)
        self.registered[event].append(handle)

    def dispatch(self, event, **kwargs):
        """
        Triggers objects that have registered to some event

        :param event: label of the event
        :type event: str

        Example::

            def on_bond(self):
                self.dispatch('bond')

        For each registered object, the bot will look for a related member
        function and call it. For example for the event
        'bond' it will look for the member function 'on_bond', etc.

        Dispatch uses weakref so that it affords the unattended deletion
        of registered objects.
        """
        assert event in self.registered.keys()  #  avoid unknown event type

        name = 'on_' + event
        for handle in self.registered[event]:
            try:
                callback = getattr(handle, name)
                callback(**kwargs)
            except ReferenceError:
                logging.debug(u"Dispatch: registered object no longer exists")

    @property
    def name(self):
        """
        Retrieves the dynamic name of this bot

        :return: The value of ``bot.name`` key in current context
        :rtype: str

        """
        return self.context.get('bot.name', 'Shelly')

    @property
    def version(self):
        """
        Retrieves the version of this bot

        :return: The value of ``bot.version`` key in current context
        :rtype: str

        """
        return self.context.get('bot.version', '*unknown*')

    def load_commands(self, *args, **kwargs):
        """
        Loads commands for this bot

        This function is a convenient proxy for the underlying shell.
        """
        self.shell.load_commands(*args, **kwargs)

    def load_command(self, *args, **kwargs):
        """
        Loads one commands for this bot

        This function is a convenient proxy for the underlying shell.
        """
        self.shell.load_command(*args, **kwargs)

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

        self.store.bond(id=self.space.get_id())

        self.dispatch('bond')

    def add_moderators(self, *args, **kwargs):
        """
        Adds moderators to the room

        This function is a proxy for the underlying space.
        """
        self.space.add_moderators(*args, **kwargs)

    def add_participants(self, *args, **kwargs):
        """
        Adds participants to the room

        This function is a proxy for the underlying space.
        """
        self.space.add_participants(*args, **kwargs)

    def dispose(self, *args, **kwargs):
        """
        Disposes all resources

        """
        self.dispatch('dispose')

        self.space.dispose(*args, **kwargs)

    def hook(self, server=None):
        """
        Connects this bot with back-end API

        :param server: web server to be used
        :type server: Server

        This function adds a route to the provided server, and
        asks the back-end service to send messages there.
        """

        if server is not None:
            logging.debug('Adding hook route to web server')
            server.add_route(
                Wrap(callable=self.get_hook(),
                     route=self.context.get('server.hook', '/hook')))

        if (self.context.get('server.binding') is not None
            and self.context.get('server.url') is not None):

            self.space.register(
                hook_url=self.context.get('server.url')
                         + self.context.get('server.hook', '/hook'))

    def get_hook(self):
        """
        Provides the hooking function to receive messages from Cisco Spark
        """
        return self.space.webhook

    def run(self, server=None):
        """
        Runs the bot

        :param server: a web server
        :type server: Server

        If a server is provided, it is run in the background. A server could
        also have been provided during initialisation, or loaded
        during configuration check.

        Alternatively, a loop is started to fetch messages.

        In both cases, this function does not return, except on interrupt.
        """

        if server is None:
            server = self.server

        self.start()

        self.hook(server=server)

        self.space.on_run()

        if server is None:
            self.space.work()

        else:
            server.run()

    def start(self):
        """
        Starts the bot
        """

        logging.warning(u'Starting the bot')

        if self.mouth is None:
            self.mouth = Queue()

        if self.inbox is None:
            self.inbox = Queue()

        if self.ears is None:
            self.ears = Queue()

        self.start_processes()

        self.say(self.context.get('bot.on_start'))
        self.on_start()

        self.dispatch('start')

    def start_processes(self):
        """
        Starts bot processes

        This function starts a separate daemonic process for each
        main component of the architecture: listener, speaker, and worker.
        """

        self.context.set('general.switch', 'on')

        p = Process(target=self.speaker.work)
        p.daemon = True
        p.start()
        self._speaker_process = p

        p = Process(target=self.worker.work)
        p.daemon = True
        p.start()
        self._worker_process = p

        p = Process(target=self.listener.work)
        p.daemon = True
        p.start()
        self._listener_process = p

    def on_start(self):
        """
        Does additional stuff on bot start

        Provide your own implementation in a sub-class where required.
        """
        pass

    def stop(self):
        """
        Stops the bot

        This function changes in the context a specific key that is monitored
        by bot components.
        """

        logging.warning(u'Stopping the bot')

        self.dispatch('stop')

        self.on_stop()

        self.say(self.context.get('bot.on_stop'))

        time.sleep(1)
        self.context.set('general.switch', 'off')

    def on_stop(self):
        """
        Do additional stuff on bot top

        Provide your own implementation in a sub-class where required.

        Note that this function is called before the actual stop, so
        you can access the shell or any other resource at will.
        """
        pass

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
            self.mouth.put(ShellBotMessage(text, content, file))

        else:
            logging.debug(u"- calling speaker directly")
            self.speaker.process(ShellBotMessage(text, content, file))

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


class ShellBotMessage(object):
    def __init__(self, text, content=None, file=None):
        self.text = text
        self.content = content
        self.file = file
