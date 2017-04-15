#!/usr/bin/env python
import colorlog
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

class ShellBot(object):

    def __init__(self,
                 context=None,
                 mouth=None,
                 inbox=None,
                 ears=None,
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

    def start(self):

        logging.warning('Starting the bot')

        self.space.connect()

        self.space.bond(
            space=self.context.get('spark.room', 'Bot under test'),
            team=self.context.get('spark.team'),
            moderators=self.context.get('spark.moderators', []),
            participants=self.context.get('spark.participants', [])
        )

        self.start_processes()

        self.space.hook()

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

        self.shell.say(self.context.get('bot.on_start'))

    def stop(self):

        logging.warning('Stopping the bot')

        self.on_stop()

        time.sleep(1)
        self.context.set('general.switch', 'off')
        self.space.unhook()

    def on_stop(self):

        self.shell.say(self.context.get('bot.on_stop'))

    def configure_from_path(self, path="settings.yaml"):
        """
        Reads configuration information

        :param path: path to the configuration file
        :type path: str

        The function loads configuration from the file and from the environment.
        Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        logging.info("Loading configuration")
        logging.info("- from '{}'".format(path))
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

        self.configure_from_dict(settings)

    def configure_from_dict(self, settings):
        """
        Reads configuration information

        :param settings: configuration information
        :type settings: dict

        The function loads configuration from the dict and from the environment.
        Port number can be set from the command line.

        Look at the file ``settings.yaml`` that is coming with this project
        """

        self.configure(settings)

        self.shell.configure(settings)
        self.space.configure(settings)

    def configure(self, settings):
        """
        Changes settings of the bot

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``bot`` and below, and update
        the context accordingly.

        >>>shell.configure({'bot': {
               'on_banner': 'Hello, I am here to help',
               }})

        This can also be written in a more compact form::

        >>>shell.configure({'bot.on_banner': 'Hello, I am here to help'})

        """

        self.context.parse(settings, 'bot', 'on_start')
        self.context.parse(settings, 'bot', 'on_stop')

# the program launched from the command line
#
if __name__ == "__main__":

    # handling logs
    #
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(asctime)-2s %(log_color)s%(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)

    logging.getLogger('').handlers = []
    logging.getLogger('').addHandler(handler)

    logging.getLogger('').setLevel(level=logging.DEBUG)

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
    logging.info("Starting web endpoint")
    run(host='0.0.0.0',
        port=context.get('server.port'),
        debug=context.get('general.DEBUG'),
        server='paste')
