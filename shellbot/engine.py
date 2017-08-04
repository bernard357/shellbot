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

from .bot import ShellBot
from .bus import Bus
from .context import Context
from .lists import ListFactory
from .listener import Listener
from .observer import Observer
from .routes.wrapper import Wrapper
from .server import Server
from .shell import Shell
from .spaces import SpaceFactory
from .speaker import Speaker
from .stores import StoreFactory


class Engine(object):
    """
    Powers multiple bots

    The engine manages the infrastructure that is used accross multiple
    bots acting in multiple spaces. It is made of an extensible set of
    components that share the same context, that is, configuration settings.

    Shellbot allows the creation of bots with a given set of commands.
    Each bot instance is bonded to a single chat space. The chat space can be
    either created by the bot itself, or the bot can join an existing space.

    The first use case is adapted when a collaboration space is created for
    semi-automated interactions between human and machines.
    In the example below, the bot controls the entire life cycle of the chat
    space. A chat space is created when the program is launched. And it is
    deleted when the program is stopped.

    Example of programmatic chat space creation::

        from shellbot import Engine, ShellBot, Context, Command
        Context.set_logger()

        # create a bot and load command
        #
        class Hello(Command):
            keyword = 'hello'
            information_message = u"Hello, World!"

        engine = Engine(command=Hello(), type='spark')

        # load configuration
        #
        engine.configure()

        # create a chat space, or connect to an existing one
        # settings of the chat space are provided
        # in the engine configuration itself
        #
        engine.bond(reset=True)

        # run the engine
        #
        engine.run()

        # delete the chat channel when the engine is stopped
        #
        engine.dispose()

    A second interesting use case is when a bot is invited to an existing chat
    space. On such an event, a new bot instance can be created and bonded
    to the chat space.

    Example of invitation to a chat space::

        def on_enter(self, channel_id):
            bot = engine.get_bot(channel_id=channel_id)

    The engine is configured by setting values in the context that is attached
    to it. This is commonly done by loading the context with a dict before the
    creation of the engine itself, as in the following example::

        context = Context({

            'bot': {
                'on_enter': 'You can now chat with Batman',
                'on_exit': 'Batman is now quitting the channel, bye',
            },

            'server': {
                'url': 'http://d9b62df9.ngrok.io',
                'hook': '/hook',
            },

        })

        engine = Engine(context=context)

        engine.configure()

    Please note that the configuration is checked and actually used on the
    call ``engine.configure()``, rather on the initialisation itself.

    When configuration statements have been stored in a separate text file
    in YAML format, then the engine can be initialised with an empty context,
    and configuration is loaded afterwards.

    Example::

        engine = Engine()
        engine.configure_from_path('/opt/shellbot/my_bot.yaml')

    When no configuration is provided to the engine, then default settings
    are considered for the engine itself, and for various components.

    For example, for a basic engine interacting in a Cisco Spark channel::

        engine = Engine(type='spark')
        engine.configure()

    When no indication is provided at all, the engine loads a space of type
    'local'.

    So, in other terms::

        engine = Engine()
        engine.configure()

    is strictly equivalent to::

        engine = Engine('local')
        engine.configure()

    In principle, the configuration of the engine is set once for the full
    life of the instance. This being said, some settings can be changed
    globally with the member function `set()`. For example::

        engine.set('bot.on_banner': 'Hello, I am here to help')

    """

    DEFAULT_SETTINGS = {

        'bot': {
            'banner.text': '$BOT_BANNER_TEXT',
            'banner.content': '$BOT_BANNER_CONTENT',
            'banner.file': '$BOT_BANNER_FILE',
            'on_enter': '$BOT_ON_ENTER',
            'on_exit': '$BOT_ON_EXIT',
        },

    }

    def __init__(self,
                 context=None,
                 settings={},
                 configure=False,
                 mouth=None,
                 ears=None,
                 fan=None,
                 space=None,
                 type=None,
                 server=None,
                 store=None,
                 command=None,
                 commands=None,
                 driver=ShellBot,
                 machine_factory=None,
                 updater_factory=None,
                 preload=0,
                 ):
        """
        Powers multiple bots

        :param context: Data shared across engine components
        :type context: Context

        :param settings: Configuration settings to apply
        :type settings: dict

        :param configure: Check configuration on initialisation
        :type configure: False (the default) or True

        :param mouth: For asynchronous outbound to the chat space
        :type mouth: Queue

        :param ears: For asynchronous inbound from the chat space
        :type ears: Queue

        :param fan: For asynchronous audit of the chat space
        :type fan: Queue

        :param type: Chat space to load for this engine. Default to 'local'
        :type type: str

        :param space: Chat space to be used by this engine
        :type space: Space

        :param server: Web server to be used by this engine
        :type server: Server

        :param command: A command to initialize the shell
        :type command: str or Command

        :param commands: A list of commands to initialize the shell
        :type commands: list of str, or list of Command

        :param driver: Instantiated for every new bot
        :type driver: class

        :param machine_factory: Provides a state machine for each bot
        :type machine_factory: MachineFactory

        :param updater_factory: Provides an updater for an audited channel
        :type updater_factory: UpdaterFactory

        :param preload: Number of existing bots to preload
        :type preload: int

        If a chat type is provided, e.g., 'spark', then one space instance is
        loaded from the SpaceFactory. Else a space of type 'local' is used.

        Example::

            engine = Engine(type='spark')

        There is also an option to inject a pre-existing space. This can be
        useful for testing purpose, or for similar advanced usage.

        Example::

            my_space = MySpecialSpace( ... )
            engine = Engine(space=my_space)

        """

        self.context = context if context else Context()

        self.mouth = mouth
        self.speaker = Speaker(engine=self)

        self.ears = ears
        self.listener = Listener(engine=self)

        self.fan = fan
        self.observer = Observer(engine=self)

        self.registered = {
            'bond': [],       # connected to a channel
            'dispose': [],    # channel will be destroyed
            'start': [],      # starting bot services
            'stop': [],       # stopping bot services
            'message': [],    # message received (with message)
            'join': [],       # joining a space (with person)
            'leave': [],      # leaving a space (with person)
            'enter': [],      # invited to a space (for the bot)
            'exit': [],       # kicked off from a space (for the bot)
            'inbound': [],    # other event received from space (with event)
        }

        self.bots = {}

        self.bots_to_load = set()  # for bots created before the engine runs

        assert space is None or type is None  # use only one
        if space:
            self.space = space
        elif type:
            self.space = SpaceFactory.get(type=type)
        else:
            self.space = SpaceFactory.get(type='local')
        self.space.context = self.context

        self.server = server

        self.shell = Shell(engine=self)

        if configure or settings:
            self.configure(settings)

        if commands:
            self.load_commands(commands)

        if command:
            self.load_command(command)

        self.driver = driver if driver else ShellBot

        self.machine_factory = machine_factory

        self.updater_factory = updater_factory

        assert preload >= 0
        self.preload = preload

    def configure_from_path(self, path="settings.yaml"):
        """
        Reads configuration information

        :param path: path to the configuration file
        :type path: str

        The function loads configuration from the file and from the
        environment. Port number can be set from the command line.

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

        """

        try:
            settings = yaml.load(stream)
        except Exception as feedback:
            logging.error(feedback)
            raise Exception(u"Unable to load valid YAML settings")

        self.configure(settings=settings)

    def configure(self, settings={}):
        """
        Checks settings

        :param settings: configuration information
        :type settings: dict

        If no settings is provided, and the context is empty, then
        ``self.DEFAULT_SETTINGS`` and ``self.space.DEFAULT_SETTINGS``
        are used instead.
        """

        self.context.apply(settings)

        if self.context.is_empty:
            self.context.apply(self.DEFAULT_SETTINGS)
            self.context.apply(self.space.DEFAULT_SETTINGS)

        self.check()

        if (self.server is None
            and self.get('server.binding') is not None):

            logging.debug(u"Adding web server")
            self.server = Server(context=self.context, check=True)

        self.space.ears = self.ears
        self.space.configure()
        self.space.connect()
        self.register('start', self.space)
        self.register('stop', self.space)

        self.list_factory = ListFactory(self.context)
        self.list_factory.configure()

        self.shell.configure()

        self.bus = Bus(self.context)
        self.bus.check()
        self.publisher = self.bus.publish()

    def check(self):
        """
        Checks settings of the engine

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``bot`` and below, and update
        the context accordingly.

        Example::

            context = Context({

                'bot': {
                    'on_enter': 'You can now chat with Batman',
                    'on_exit': 'Batman is now quitting the channel, bye',
                },

                'server': {
                    'url': 'http://d9b62df9.ngrok.io',
                    'hook': '/hook',
                },

            })
            engine = Engine(context=context)
            engine.check()

        """
        self.context.check('bot.banner.text', filter=True)
        self.context.check('bot.banner.content', filter=True)
        self.context.check('bot.banner.file', filter=True)

        self.context.check('bot.on_enter', filter=True)
        self.context.check('bot.on_exit', filter=True)

    def get(self, key, default=None):
        """
        Retrieves the value of one configuration key

        :param key: name of the value
        :type key: str

        :param default: default value
        :type default: any serializable type is accepted

        :return: the actual value, or the default value, or None

        Example::

            message = engine.get('bot.on_start')

        This function is safe on multiprocessing and multithreading.

        """
        return self.context.get(key, default)

    def set(self, key, value):
        """
        Changes the value of one configuration key

        :param key: name of the value
        :type key: str

        :param value: new value
        :type value: any serializable type is accepted

        Example::

            engine.set('bot.on_start', 'hello world')

        This function is safe on multiprocessing and multithreading.

        """
        self.context.set(key, value)

    @property
    def name(self):
        """
        Retrieves the dynamic name of this bot

        :return: The value of ``bot.name`` key in current context
        :rtype: str

        """
        return self.get('bot.name', 'Shelly')

    @property
    def version(self):
        """
        Retrieves the version of this bot

        :return: The value of ``bot.version`` key in current context
        :rtype: str

        """
        return self.get('bot.version', '*unknown*')

    def register(self, event, instance):
        """
        Registers an object to process an event

        :param event: label, such as 'start' or 'bond'
        :type event: str

        :param instance: an object that will handle the event
        :type instance: object

        This function is used to propagate events to any module
        that may need it via callbacks.

        On each event, the engine will look for a related member function
        in the target instance and call it. For example for the event
        'start' it will look for the member function 'on_start', etc.

        Following standard events can be registered:

        - 'bond' - when the bot has connected to a chat channel

        - 'dispose' - when resources, including chat space, will be destroyed

        - 'start' - when the engine is started

        - 'stop' - when the engine is stopped

        - 'join' - when a person is joining a space

        - 'leave' - when a person is leaving a space

        Example::

            def on_init(self):
                self.engine.register('bond', self)  # call self.on_bond()
                self.engine.register('dispose', self) # call self.on_dispose()

        If the function is called with an unknown label, then a new list
        of registered callbacks will be created for this event. Therefore the
        engine can be used for the dispatching of any custom event.

        Example::

            self.engine.register('input', processor)  # for processor.on_input()
            ...
            received = 'a line of text'
            self.engine.dispatch('input', received)

        Registration uses weakref so that it affords the unattended deletion
        of registered objects.

        """
        logging.debug(u"Registering to '{}' dispatch".format(event))

        assert event not in (None, '')
        assert isinstance(event, string_types)
        if event not in self.registered.keys():
            self.registered[event] = []

        name = 'on_' + event
        callback = getattr(instance, name)
        assert callable(callback)  # ensure the event is supported

        handle = weakref.proxy(instance)
        self.registered[event].append(handle)

        if len(self.registered[event]) > 1:
            logging.debug(u"- {} objects registered to '{}'".format(
                len(self.registered[event]), event))

        else:
            logging.debug(u"- 1 object registered to '{}'".format(event))

    def dispatch(self, event, **kwargs):
        """
        Triggers objects that have registered to some event

        :param event: label of the event
        :type event: str

        Example::

            def on_bond(self):
                self.dispatch('bond', bot=this_bot)

        For each registered object, the function will look for a related member
        function and call it. For example for the event
        'bond' it will look for the member function 'on_bond', etc.

        Dispatch uses weakref so that it affords the unattended deletion
        of registered objects.
        """
        assert event in self.registered.keys()  # avoid unknown event type

        if len(self.registered[event]) > 1:
            logging.debug(u"Dispatching '{}' to {} objects".format(
                event, len(self.registered[event])))

        elif len(self.registered[event]) > 0:
            logging.debug(u"Dispatching '{}' to 1 object".format(event))

        else:
            logging.debug(u"Dispatching '{}', nothing to do".format(event))
            return

        name = 'on_' + event
        for handle in self.registered[event]:
            try:
                callback = getattr(handle, name)
                callback(**kwargs)
            except ReferenceError:
                logging.debug(u"- registered object no longer exists")

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

    def hook(self, server=None):
        """
        Connects this engine with back-end API

        :param server: web server to be used
        :type server: Server

        This function adds a route to the provided server, and
        asks the back-end service to send messages there.
        """

        if server is not None:
            logging.debug('Adding hook route to web server')
            server.add_route(
                Wrapper(callable=self.get_hook(),
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
        Runs the engine

        :param server: a web server
        :type server: Server

        If a server is provided, it is ran in the background. A server could
        also have been provided during initialisation, or loaded
        during configuration check.

        If no server instance is available, a loop is started
        to fetch messages in the background.

        In both cases, this function does not return, except on interrupt.
        """

        if server is None:
            server = self.server

        self.start()

        self.hook(server=server)

        if server is None:
            self.space.run()

        else:
            p = Process(target=server.run)
            p.daemon = True
            p.start()
            self._server_process = p

            try:
                self._server_process.join()
            except KeyboardInterrupt:
                logging.error(u"Aborted by user")

        self.stop()

    def start(self):
        """
        Starts the engine
        """

        logging.warning(u'Starting the bot')

        for channel in self.space.list_group_channels(quantity=self.preload):
            self.bots_to_load.add(channel.id)  # handled by the listener

        if self.mouth is None:
            self.mouth = Queue()

        if self.ears is None:
            self.ears = Queue()
            self.space.ears = self.ears

        if self.fan is None and self.updater_factory:
            self.fan = Queue()
        self.space.fan = self.fan

        self.start_processes()

        self.on_start()

        self.dispatch('start')

    def start_processes(self):
        """
        Starts the engine processes

        This function starts a separate process for each
        main component of the architecture: listener, speaker, etc.
        """

        self.context.set('general.switch', 'on')

        self.speaker.start()
        self.listener.start()
        self.publisher.start()
        self.observer.start()

    def on_start(self):
        """
        Does additional stuff when the engine is started

        Provide your own implementation in a sub-class where required.
        """
        pass

    def stop(self):
        """
        Stops the engine

        This function changes in the context a specific key that is monitored
        by bot components.
        """

        logging.warning(u'Stopping the bot')

        self.dispatch('stop')

        self.on_stop()

        logging.debug(u"Switching off")
        self.context.set('general.switch', 'off')
        time.sleep(1)

        try:
            self.listener.join()
        except AssertionError:
            pass  # if listener process was not started

    def on_stop(self):
        """
        Does additional stuff when the engine is stopped

        Provide your own implementation in a sub-class where required.

        Note that some processes may have been killed at the moment of this
        function call. This is likely to happen when end-user hits Ctl-C on
        the keyboard for example.
        """
        pass

    def bond(self,
             title=None,
             reset=False,
             participants=None,
             **kwargs):
        """
        Bonds to a channel

        :param title: title of the target channel
        :type: title: str

        :param reset: if True, delete previous channel and re-create one
        :type reset: bool

        :param participants: the list of initial participants (optional)
        :type participants: list of str

        :return: Channel or None

        This function creates a channel, or connect to an existing one.
        If no title is provided, then the generic title configured for the
        underlying space is used instead.

        For example::

            channel = engine.bond('My crazy channel')
            if channel:
                ...

        Note: this function asks the listener to load a new bot in its cache
        on successful channel creation or lookup. In other terms, this function
        can be called safely from any process for the creation of a channel.
        """
        if title in (None, ''):
            title=self.space.configured_title()

        logging.debug(u"Bonding to channel '{}'".format(title))

        channel = self.space.get_by_title(title=title)
        if channel and not reset:
            logging.debug(u"- found existing channel")

            # ask explicitly the listener to load the bot
            if self.ears is None:
                self.ears = Queue()
                self.space.ears = self.ears

        else:
            if channel and reset:
                logging.debug(u"- deleting existing channel")
                self.space.delete(id=channel.id)

            logging.debug(u"- creating channel '{}'".format(title))
            channel = self.space.create(title=title, **kwargs)

            if not channel:
                logging.error("Unable to create channel")
                return

            if not participants:
                participants = self.space.get('participants', [])
            self.space.add_participants(id=channel.id, persons=participants)

        self.bots_to_load.add(channel.id)  # handled by the listener

        return channel

    def dispose(self,
                title=None,
                **kwargs):
        """
        Destroys a named channel

        :param title: title of the target channel
        :type: title: str

        """
        if title in (None, ''):
            title=self.space.configured_title()

        logging.debug(u"Disposing channel '{}'".format(title))

        channel = self.space.get_by_title(title=title)
        if channel:
            self.space.delete(id=channel.id, **kwargs)

    def enumerate_bots(self):
        """
        Enumerates all bots
        """
        for id in self.bots.keys():
            yield self.bots[id]

    def get_bot(self, channel_id=None, **kwargs):
        """
        Gets a bot by id

        :param channel_id: The unique id of the target chat space
        :type channel_id: str

        :return: a bot instance, or None

        This function receives the id of a chat space, and returns
        the related bot.

        If no id is provided, then the underlying space is asked to provide
        with a default channel, as set in overall configuration.

        Note: this function should not be called from multiple processes,
        because this would create one bot per process. Use the function
        ``engine.bond()`` for the creation of a new channel.
        """
        if not channel_id:
            channel = self.bond(**kwargs)
            if not channel:
                return
            channel_id = channel.id

        logging.debug(u"Getting bot {}".format(channel_id))
        if channel_id and channel_id in self.bots.keys():
            logging.debug(u"- found matching bot instance")
            return self.bots[channel_id]

        bot = self.build_bot(id=channel_id, driver=self.driver)

        if bot and bot.id:
            logging.debug(u"- remembering bot {}".format(bot.id))
            self.bots[bot.id] = bot
            self.set('bots.ids', self.bots.keys())   # for the observer

        bot.bond()

        bot.on_enter()

        return bot

    def build_bot(self, id=None, driver=ShellBot):
        """
        Builds a new bot

        :param id: The unique id of the target space
        :type id: str

        :return: a ShellBot instance, or None

        This function receives the id of a chat space, and returns
        the related bot.
        """
        logging.debug(u"- building bot instance")
        bot = driver(engine=self, channel_id=id)

        self.initialize_store(bot=bot)

        bot.machine = self.build_machine(bot=bot)

        self.on_build(bot)

        return bot

    def on_build(self, bot):
        """
        Extends the building of a new bot instance

        :param bot: a new bot instance
        :type bot: ShellBot

        Provide your own implementation in a sub-class where required.

        Example::

            on_build(self, bot):
                bot.secondary_machine = Input(...)
        """
        pass

    def build_store(self, channel_id=None):
        """
        Builds a store for this bot

        :param channel_id: Identifier of the target chat space
        :type channel_id: str

        :return: a Store instance, or None

        This function receives an identifier, and returns
        a store bound to it.
        """
        logging.debug(u"- building data store")
        return StoreFactory.get(type='memory')

    def initialize_store(self, bot):
        """
        Copies engine settings to the bot store
        """
        logging.debug(u"Initializing bot store")

        settings = self.get('bot.store', {})
        if settings:
            logging.debug(u"- initializing store from general settings")
            for (key, value) in settings.items():
                bot.store.remember(key, value)

        if bot.id:
            label = "store.{}".format(bot.id)
            settings = self.get(label, {})
            if settings:
                logging.debug(u"- initializing store from bot settings")
                for (key, value) in settings.items():
                    bot.store.remember(key, value)

    def build_machine(self, bot):
        """
        Builds a state machine for this bot

        :param bot: The target bot
        :type bot: ShellBot

        :return: a Machine instance, or None

        This function receives a bot, and returns
        a state machine bound to it.
        """
        if self.machine_factory:
            logging.debug(u"- building state machine")
            machine = self.machine_factory.get_machine(bot=bot)
            return machine

        return None

    def build_updater(self, id):
        """
        Builds an updater for this channel

        :param id: The identifier of an audited channel
        :type id: str

        :return: an Updater instance, or None

        This function receives a bot, and returns
        a state machine bound to it.
        """
        if self.updater_factory:
            logging.debug(u"- building updater")
            updater = self.updater_factory.get_updater(id=id)
            return updater

        return None

    def on_enter(self, join):
        """
        Bot has been invited to a chat space

        :param join: The join event received from the chat space
        :type join: Join

        Provide your own implementation in a sub-class where required.

        Example::

            on_enter(self, join):
                mailer.post(u"Invited to {}".format(join.space_title))
        """
        pass

    def on_exit(self, leave):
        """
        Bot has been kicked off from a chat space

        :param leave: The leave event received from the chat space
        :type leave: Leave

        Provide your own implementation in a sub-class where required.

        Example::

            on_exit(self, leave):
                mailer.post(u"Kicked off from {}".format(leave.space_title))
        """
        pass
