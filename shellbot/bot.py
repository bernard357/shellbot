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
                 context,
                 mouth=None,
                 inbox=None,
                 ears=None,
                 space=None,
                 store=None):

        self.context = context

        self.mouth = mouth if mouth else Queue()
        self.inbox = inbox if inbox else Queue()
        self.ears = ears if ears else Queue()

        self.space = space if space else SparkSpace(context=context,
                                                    ears=ears)
        self.store = store

        self.shell = Shell(self.context, self.mouth, self.inbox)
        self.shell.load_default_commands()
        commands = self.context.get('bot.commands')
        if commands:
            self.shell.load_commands(commands)

        self.speaker = Speaker(self.mouth, self.space)
        self.worker = Worker(self.inbox, self.shell)
        self.listener = Listener(self.ears, self.shell)

    def start(self):
        logging.info('Starting all threads')
        p = Process(target=self.speaker.work, args=(self.context,))
        p.daemon = True
        p.start()
        self.speaker.process = p

        p = Process(target=self.worker.work, args=(self.context,))
        p.daemon = True
        p.start()
        self.worker.process = p

        p = Process(target=self.listener.work, args=(self.context,))
        p.daemon = True
        p.start()
        self.listener.process = p

    def stop(self):
        logging.info('Stopping all threads')
        self.context.set('general.switch', 'off')
        self.listener.process.join()
        self.worker.process.join()
        self.speaker.process.join()

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

        if "bot" not in settings:
            raise KeyError("Missing bot: configuration information")

        if "name" not in settings['bot']:
            raise KeyError("Missing bot.name: configuration information")

        if "spark" not in settings:
            raise KeyError("Missing spark: configuration information")

        if "space" not in settings['spark']:
            raise KeyError("Missing space: configuration information")

        if "moderators" not in settings['spark']:
            raise KeyError("Missing moderators: configuration information")

        if "mode" not in settings['spark']:
            settings['spark']['mode'] = 'webhook'

        if 'CISCO_SPARK_PLUMBERY_BOT' not in settings['spark']:
            token = os.environ.get('CISCO_SPARK_PLUMBERY_BOT')
            if token is None:
                raise KeyError("Missing CISCO_SPARK_PLUMBERY_BOT in the environment")
            settings['spark']['CISCO_SPARK_PLUMBERY_BOT'] = token

        if 'CISCO_SPARK_TOKEN' not in settings['spark']:
            token = os.environ.get('CISCO_SPARK_TOKEN')
            if token is None:
                logging.warning("Missing CISCO_SPARK_TOKEN, reduced functionality")
                token = settings['spark']['CISCO_SPARK_PLUMBERY_BOT']
            settings['spark']['CISCO_SPARK_TOKEN'] = token

        if "server" not in settings:
            raise KeyError("Missing server: configuration information")

        if "url" not in settings['server']:
            raise KeyError("Missing url: configuration information")

        if len(sys.argv) > 1:
            try:
                port_number = int(sys.argv[1])
            except:
                raise ValueError("Invalid port_number specified")
        elif "port" in settings['server']:
            port_number = int(settings['server']['port'])
        else:
            port_number = 80
        settings['server']['port'] = port_number

        if 'debug' in settings:
            debug = settings['debug']
        else:
            debug = os.environ.get('DEBUG', False)
        settings['debug'] = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)

        self.context.apply(settings)

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
