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

import json
import logging
import os
from multiprocessing import Process, Queue
import requests
from requests_toolbelt import MultipartEncoder
import sys
import time
import yaml
from bottle import route, run, request, abort

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
                 settings=None,
                 space=None,
                 store=None):

        self.context = context if context else Context()

        self.mouth = mouth if mouth else Queue()
        self.inbox = inbox if inbox else Queue()
        self.ears = ears if ears else Queue()

        self.space = space if space else SparkSpace(context=self.context,
                                                    ears=self.ears)
        self.store = store

        self.shell = Shell(self.context, self.mouth, self.inbox)

        self.speaker = Speaker(self.mouth, self.space)
        self.worker = Worker(self.inbox, self.shell)
        self.listener = Listener(self.ears, self.shell)

        if settings is not None:
            self.configure(settings)

    def configure_from_path(self, path="settings.yaml"):
        """
        Reads configuration information

        :param path: path to the configuration file
        :type path: str

        The function loads configuration from the file and from the environment.
        Port number can be set from the command line.

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

        The function loads configuration from the file and from the environment.
        Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        try:
            settings = yaml.load(stream)
        except Exception as feedback:
            logging.error(str(feedback))
            sys.exit(1)

        self.configure(settings)

    def configure(self, settings):
        """
        Reads configuration information

        :param settings: configuration information
        :type settings: dict

        The function loads configuration from the dict and from the environment.
        Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        self.configure_from_dict(settings)

        self.shell.configure(settings)
        self.space.configure(settings)

    def configure_from_dict(self, settings):
        """
        Changes settings of the bot

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``bot`` and below, and update
        the context accordingly. It also reads hook parameters under ``server``.

        >>>shell.configure({

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

        self.context.parse(settings, 'bot', 'on_start')
        self.context.parse(settings, 'bot', 'on_stop')

        self.context.parse(settings, 'server', 'url')
        self.context.parse(settings, 'server', 'hook')

    def load_commands(self, *args, **kwargs):
        """
        Loads commands for this bot

        This function is a convenient proxy for the underlying shell.
        """
        self.shell.load_commands(*args, **kwargs)

    def bond(self, reset=False):
        """
        Bonds to a room

        :param reset: if True, delete previous room and re-create one
        :type reset: bool

        This function creates a room, or connect to an existing one.
        """
        self.space.connect()

        if reset:
            self.space.dispose(self.context.get('spark.room'))

        self.space.bond(
            space=self.context.get('spark.room', 'Bot under test'),
            team=self.context.get('spark.team'),
            moderators=self.context.get('spark.moderators', []),
            participants=self.context.get('spark.participants', [])
        )

    def hook(self, server):
        """
        Connects this bot with Cisco Spark

        :param server: web server to be used
        :type server: Server

        This function adds a route to the provided server, and
        asks Cisco Spark to send messages there.
        """
        server.add_route(
            Wrapper(route=self.context.get('server.hook', '/hook'),
                    callable=self.space.webhook))

        assert self.context.get('server.url') is not None
        self.space.hook(
            self.context.get('server.url')
            +self.context.get('server.hook', '/hook'))

    def run(self, server=None):
        """
        Runs the bot

        :param server: a web server

        If a server is provided, it is ran in the background. Else
        a pulling loop is started instead to get messages.

        In both cases, this function does not return, except on interrupt.
        """
        self.start()

        if server is None:
            self.space.pull_for_ever()

        else:
            server.run()

    def start(self):

        logging.warning(u'Starting the bot')

        self.context.set('general.switch', 'on')
        self.start_processes()

        self.shell.say(self.context.get('bot.on_start'))
        self.on_start()

    def start_processes(self):

        p = Process(target=self.speaker.work, args=(self.context,))
        p.daemon = True
        p.start()
        self._speaker_process = p

        p = Process(target=self.worker.work, args=(self.context,))
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

        logging.warning(u'Stopping the bot')

        self.shell.say(self.context.get('bot.on_stop'))
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

# the program launched from the command line
#
if __name__ == "__main__":

    # handling logs
    #
    Context.set_logger()

    # the safe-thread store that is shared across components
    #
    context = Context()
    context.set('bot.version', '0.1 alpha')

    # create the bot
    #
    bot = ShellBot(context)

    # read configuration file, look at the environment, and update context
    #
    bot.configure()

#        try:
#            context.set('bot.id', space.get_bot()['id'])
#        except:
#            pass


    # create a clean environment for the demo
    #
    delete_room(context)

    # start the bot
    #
    bot.start()

    # create room if needed, and get its id
    #
    get_room(context)

    # connect to Cisco Spark
    #
    if context.get('spark.mode') == 'pull':
        w = Process(target=pull_from_spark)
        w.daemon = True
        w.start()

    else:
        register_hook(context)

    # ready to receive updates
    #
    logging.info(u"Starting web endpoint")
    run(host='0.0.0.0',
        port=context.get('server.port'),
        debug=context.get('general.DEBUG'),
        server='paste')
