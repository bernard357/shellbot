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

from context import Context
from shell import Shell
from listener import Listener
from space import SparkSpace
from speaker import Speaker
from worker import Worker
from routes.wrapper import Wrapper


class ShellBot(object):

    def __init__(self,
                 context=None,
                 mouth=None,
                 inbox=None,
                 ears=None,
                 check=False,
                 space=None,
                 store=None):

        self.context = context if context else Context()

        self.mouth = mouth if mouth else Queue()
        self.inbox = inbox if inbox else Queue()
        self.ears = ears if ears else Queue()

        self.space = space if space else SparkSpace(context=self.context,
                                                    ears=self.ears)
        self.store = store

        self.shell = Shell(bot=self)

        self.speaker = Speaker(self.mouth, self.space)
        self.worker = Worker(bot=self)
        self.listener = Listener(self.ears, self.shell)

        if check:
            self.configure()

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

    def configure(self, settings={}):
        """
        Checks settings

        :param settings: configuration information
        :type settings: dict

        The function loads configuration from the dict and from the
        environment. Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        self.configure_from_dict(settings)

        self.shell.configure(settings)
        self.space.configure(settings)

        self.space.connect()

    def configure_from_dict(self, settings):
        """
        Changes settings of the bot

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``bot`` and below, and update
        the context accordingly.
        It also reads hook parameters under ``server``.

        >>>shell.configure_fom_dict({

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

        >>>shell.configure({'bot.on_banner': 'Hello, I am here to help'})

        """

        self.context.apply(settings)
        self.context.check('bot.on_start')
        self.context.check('bot.on_stop')
        self.context.check('server.url')
        self.context.check('server.hook')

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
            self.dispose(self.context.get('spark.room'))

        def remember_room_id(id):
            self.context.set('room.id', id)

        self.space.bond(
            room=self.context.get('spark.room', 'Bot under test'),
            team=self.context.get('spark.team'),
            moderators=self.context.get('spark.moderators', []),
            participants=self.context.get('spark.participants', []),
            callback=remember_room_id
        )

    def add_moderators(self, *args, **kwargs):
        """
        Adds moderators to the room

        This function is a convenient proxy for the underlying space.
        """
        self.space.add_moderators(*args, **kwargs)

    def add_participants(self, *args, **kwargs):
        """
        Adds participants to the room

        This function is a convenient proxy for the underlying space.
        """
        self.space.add_participants(*args, **kwargs)

    def dispose(self, *args, **kwargs):
        """
        Disposes the room

        This function is a convenient proxy for the underlying space.
        """
        self.space.dispose(*args, **kwargs)

    def hook(self, server=None):
        """
        Connects this bot with Cisco Spark

        :param server: web server to be used
        :type server: Server

        This function adds a route to the provided server, and
        asks Cisco Spark to send messages there.
        """

        if server is not None:
            logging.debug('Adding hook route to web server')
            server.add_route(
                Wrapper(route=self.context.get('server.hook', '/hook'),
                        callable=self.get_hook()))

        assert self.context.get('server.url') is not None
        self.space.hook(
            self.context.get('server.url')
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

        If a server is provided, it is run in the background. Else
        a pulling loop is started instead to get messages.

        In both cases, this function does not return, except on interrupt.
        """
        self.start()

        if server is None:
            self.space.pull_for_ever()

        else:
            server.run()

    def start(self):
        """
        Starts the bot
        """

        logging.warning(u'Starting the bot')

        self.context.set('general.switch', 'on')
        self.start_processes()

        self.say(self.context.get('bot.on_start'))
        self.on_start()

    def start_processes(self):
        """
        Starts bot processes

        This function starts a separate daemonic process for each
        main component onf the architecture: listener, speaker, and worker.
        """

        p = Process(target=self.speaker.work, args=(self.context,))
        p.daemon = True
        p.start()
        self._speaker_process = p

        p = Process(target=self.worker.work)
        p.daemon = True
        p.start()
        self._worker_process = p

        p = Process(target=self.listener.work, args=(self.context,))
        p.daemon = True
        p.start()
        self._listener_process = p

    def on_start(self):
        """
        Do additional stuff on bot start

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

        self.say(self.context.get('bot.on_stop'))
        self.on_stop()

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

    def say(self, message, markdown=None, file=None):
        """
        Sends a response back to the room

        :param message: Plain text message
        :type message: str or None

        :param markdown: A message using Markdown
        :type markdown: str or None

        :param file: path or URL to a file to attach
        :type file: str or None

        """
        if message in (None, ''):
            return

        if self.mouth:
            if markdown or file:
                logging.info(u"Bot says: {}".format(message))
                self.mouth.put(ShellBotMessage(message, markdown, file))
            else:
                logging.info(u"Bot says: {}".format(message))
                self.mouth.put(message)
        else:
            logging.info(u"Bot says: {}".format(message))


class ShellBotMessage(object):
    def __init__(self, message, markdown=None, file=None):
        self.message = message
        self.markdown = markdown
        if message is not None and markdown is not None:
            self.markdown = message+'\n\n'+markdown
        self.file = file
