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

from .context import Context
from .shell import Shell
from .listener import Listener
from .server import Server
from .bot import ShellBot
from .spaces import SpaceFactory
from .speaker import Speaker
from .stores import StoreFactory
from .worker import Worker
from .routes.wrapper import Wrapper


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

        engine = Engine(command=Hello())

        # load configuration
        #
        engine.configure()

        # create a chat space, or connect to an existing one
        # settings of the chat space are provided
        # in the engine configuration itself
        #
        bot = ShellBot(engine=engine)
        bot.bond(reset=True)

        # run the engine
        #
        engine.run()

        # delete the chat room when the engine is stopped
        #
        bot.dispose()

    A second interesting use case is when a bot is invited to an existing chat
    space. On such an event, a new bot instance can be created and bonded
    to the chat space.

    Example of invitation to a chat space::

        def on_enter(self, space_id):
            bot = ShellBot(engine=my_engine)
            bot.use_space(id=space_id)
            return bot

    """

    DEFAULT_SETTINGS = {

        'bot': {
            'on_enter': '$BOT_ON_ENTER',
            'on_exit': '$BOT_ON_EXIT',
        },

        'spark': {
            'room': '$CHAT_ROOM_TITLE',
            'moderators': '$CHAT_ROOM_MODERATORS',
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
                 settings={},
                 configure=False,
                 mouth=None,
                 inbox=None,
                 ears=None,
                 space=None,
                 type=None,
                 server=None,
                 store=None,
                 command=None,
                 commands=None,
                 ):
        """
        Powers multiple bots

        :param context: Data shared across engine components
        :type context: Context

        :param settings: Configuration settings to apply
        :type settings: dict

        :param configure: Check configuration on initialisation
        :type configure: False (the default) or True

        :param mouth: For asynchronous transmission to the chat space
        :type mouth: Queue

        :param inbox: For asynchronous processing of commands
        :type inbox: Queue

        :param ears: For asynchronous updates from the chat space
        :type ears: Queue

        :param space: Chat space to be used by this engine
        :type space: Space

        :param type: Chat space to load for this engine
        :type type: str

        :param server: Web server to be used by this engine
        :type server: Server

        :param store: Data store to be used by this engine
        :type store: Store

        :param command: A command to initialize the shell
        :type command: str or Command

        :param commands: A list of commands to initialize the shell
        :type commands: list of str, or list of Command

        """

        self.context = context if context else Context()

        self.mouth = mouth
        self.speaker = Speaker(engine=self)

        self.inbox = inbox
        self.worker = Worker(engine=self)

        self.ears = ears
        self.listener = Listener(engine=self)

        self.subscribed = {
            'bond': [],       # connected to a space
            'dispose': [],    # space will be destroyed
            'start': [],      # starting bot services
            'stop': [],       # stopping bot services
            'message': [],    # message received (with message)
            'attachment': [], # attachment received (with attachment)
            'join': [],       # joining a space (with person)
            'leave': [],      # leaving a space (with person)
            'enter': [],      # invited to a space (for the bot)
            'exit': [],       # kicked off from a space (for the bot)
            'inbound': [],    # other event received from space (with event)
        }

        self.bots = {}

        assert space is None or type is None  # use only one
        if type:
            space = SpaceFactory.get(type=type)
        self.space = space
        if self.space:
            self.space.context = self.context

        self.server = server

        self.shell = Shell(engine=self)

        if configure or settings:
            self.configure(settings)

        if commands:
            self.load_commands(commands)

        if command:
            self.load_command(command)

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

        self.shell.configure()

        if self.space is None:
            self.space = SpaceFactory.build(context=self.context, ears=self.ears)

        self.space.configure()

        self.space.connect()

        if (self.server is None
            and self.context.get('server.binding') is not None):

            logging.debug(u"Adding web server")
            self.server = Server(context=self.context, check=True)

    def configure_from_dict(self, settings):
        """
        Changes settings of the engine

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``bot`` and below, and update
        the context accordingly.
        It also reads hook parameters under ``server``::

            engine.configure_fom_dict({

                'bot': {
                    'on_enter': 'You can now chat with Batman',
                    'on_exit': 'Batman is now quitting the room, bye',
                },

                'server': {
                    'url': 'http://d9b62df9.ngrok.io',
                    'hook': '/hook',
                },

            })

        This can also be written in a more compact form::

            engine.configure_from_dict(
                {'bot.on_banner': 'Hello, I am here to help'})

        """

        self.context.apply(settings)
        self.context.check('bot.on_enter', '', filter=True)
        self.context.check('bot.on_exit', '', filter=True)

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

    def subscribe(self, event, instance):
        """
        Registers an object to process an event

        :param event: label, such as 'start' or 'bond'
        :type event: str

        :param instance: an object that will handle the event
        :type instance: object

        This function is used to propagate bot events to any module
        that may need it.

        On each event, the bot will look for a related member function
        in the target instance and call it. For example for the event
        'start' it will look for the member function 'on_start', etc.

        Following standard events can be subscribed:

        - 'bond' - when the bot has connected to a chat space

        - 'dispose' - when resources, including chat space, will be destroyed

        - 'start' - when bot services are started

        - 'stop' - when bot services are stopped

        - 'join' - when a person is joining a space

        - 'leave' - when a person is leaving a space

        Example::

            def on_init(self):
                self.engine.subscribe('bond', self)  # call self.on_bond()
                self.engine.subscribe('dispose', self) # call self.on_dispose()

        If the function is called with an unknown label, then a new list
        of subscribers will be created for this event. Therefore the bot
        can be used for the dispatching of any custom event.

        Example::

            self.engine.subscribe('input', processor)  # for processor.on_input()
            ...
            received = 'a line of text'
            self.engine.dispatch('input', received)

        Registration uses weakref so that it affords the unattended deletion
        of subscribed objects.

        """
        logging.debug(u"Registering to '{}' dispatch".format(event))

        assert event not in (None, '')
        assert isinstance(event, string_types)
        if event not in self.subscribed.keys():
            self.subscribed[event] = []

        name = 'on_' + event
        callback = getattr(instance, name)
        assert callable(callback)  # ensure the event is supported

        handle = weakref.proxy(instance)
        self.subscribed[event].append(handle)

        if len(self.subscribed[event]) > 1:
            logging.debug(u"- {} objects subscribed to '{}'".format(
                len(self.subscribed[event]), event))

        else:
            logging.debug(u"- 1 object subscribed to '{}'".format(event))

    def dispatch(self, event, **kwargs):
        """
        Triggers objects that have subscribed to some event

        :param event: label of the event
        :type event: str

        Example::

            def on_bond(self):
                self.dispatch('bond')

        For each subscribed object, the function will look for a related member
        function and call it. For example for the event
        'bond' it will look for the member function 'on_bond', etc.

        Dispatch uses weakref so that it affords the unattended deletion
        of subscribed objects.
        """
        assert event in self.subscribed.keys()  # avoid unknown event type

        if len(self.subscribed[event]) > 1:
            logging.debug(u"Dispatching '{}' to {} objects".format(
                event, len(self.subscribed[event])))

        elif len(self.subscribed[event]) > 0:
            logging.debug(u"Dispatching '{}' to 1 object".format(event))

        else:
            logging.debug(u"Dispatching '{}', nothing to do".format(event))
            return

        name = 'on_' + event
        for handle in self.subscribed[event]:
            try:
                callback = getattr(handle, name)
                callback(**kwargs)
            except ReferenceError:
                logging.debug(u"- subscribed object no longer exists")

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

        self.space.on_start()

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

        if self.mouth is None:
            self.mouth = Queue()

        if self.inbox is None:
            self.inbox = Queue()

        if self.ears is None:
            self.ears = Queue()
            self.space.ears = self.ears

        self.start_processes()

        self.on_start()

        self.dispatch('start')

    def start_processes(self):
        """
        Starts the engine processes

        This function starts a separate process for each
        main component of the architecture: listener, speaker, and worker.
        """

        self.context.set('general.switch', 'on')

        self._speaker_process = self.speaker.start()
        self._worker_process = self.worker.start()
        self._listener_process = self.listener.start()

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

        logging.debug(u"- dispatching 'stop' event")
        self.dispatch('stop')

        logging.debug(u"- running on_stop()")
        self.on_stop()

        logging.debug(u"- switching off")
        self.context.set('general.switch', 'off')
        time.sleep(1)

    def on_stop(self):
        """
        Does additional stuff when the engine is stopped

        Provide your own implementation in a sub-class where required.

        Note that this function is called before the actual stop, so
        you can access the shell or any other resource at will.
        """
        pass

    def get_bot(self, space_id=None):
        """
        Gets a bot by id

        :param space_id: The unique id of the target chat space
        :type space_id: str

        :return: a bot instance, or None

        This function receives the id of a chat space, and returns
        the related bot.
        """
        logging.debug(u"Getting bot {}".format(space_id))
        if space_id and space_id in self.bots.keys():
            logging.debug(u"- found matching bot instance")
            return self.bots[space_id]

        bot = self.build_bot(space_id)

        if bot:
            self.bots[bot.space_id] = bot

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
        bot = driver(engine=self, space_id=id)

        bot.space = self.build_space(space_id=id)

        bot.store = self.build_store(space_id=id)

        logging.debug(u"- building state machine")
        bot.machine = self.build_machine(bot=bot)

        self.on_build(bot)

        return bot

    def build_space(self, space_id=None):
        """
        Builds a space for this bot

        :param space_id: Identifier of the target chat space
        :type space_id: str

        :return: a Space instance, or None

        This function receives an identifier, and returns
        a space bound to it.
        """
        logging.debug(u"- building space instance")
        if space_id:
            space = SpaceFactory.build(context=self.context, ears=self.ears)
            space.configure()
            space.connect()
            space.use_space(id=space_id)
            return space
        else:
            return self.space

    def build_store(self, space_id=None):
        """
        Builds a store for this bot

        :param space_id: Identifier of the target chat space
        :type space_id: str

        :return: a Store instance, or None

        This function receives an identifier, and returns
        a store bound to it.
        """
        logging.debug(u"- building data store")
        return StoreFactory.get(type='memory')

    def build_machine(self, bot):
        """
        Builds a state machine for this bot

        :param bot: The target bot
        :type bot: ShellBot

        :return: a Machine instance, or None

        This function receives a bot, and returns
        a state machine bound to it.
        """
        return None

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

    def bond(self, reset):
        """
        Bonds this engine to a single space
        """
        bot = self.get_bot()
        bot.bond(reset=True)
        return bot

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

