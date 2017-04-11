#!/usr/bin/env python

import colorlog
import unittest
import logging
import os
from multiprocessing import Process, Queue
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.worker import Worker
from shellbot.shell import Shell


class WorkerTests(unittest.TestCase):

    def test_static(self):

        logging.info('*** Static test ***')

        mouth = Queue()
        inbox = Queue()

        context = Context()
        shell = Shell(context, mouth, inbox)
        shell.load_default_commands()
        worker = Worker(inbox, shell)

        worker_process = Process(target=worker.work, args=(context,))
        worker_process.daemon = True
        worker_process.start()

        worker_process.join(1.0)
        if worker_process.is_alive():
            logging.info('Stopping worker')
            context.set('general.switch', 'off')
            worker_process.join()

        self.assertFalse(worker_process.is_alive())
        self.assertEqual(context.get('worker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        mouth = Queue()
        inbox = Queue()
        inbox.put(('echo', 'hello world'))
        inbox.put(('help', 'help'))
        inbox.put(('pass', ''))
        inbox.put(('sleep', '2'))
        inbox.put(('version', ''))
        inbox.put(('unknownCommand', ''))
        inbox.put(Exception('EOQ'))

        context = Context()
        shell = Shell(context, mouth, inbox)
        shell.load_default_commands()
        worker = Worker(inbox, shell)

        worker.work(context)

        self.assertEqual(context.get('worker.counter'), 6)

        self.assertEqual(mouth.get(), 'hello world')

        self.assertEqual(
            mouth.get(),
            'help - Lists available commands and related usage information.')
        self.assertEqual(
            mouth.get(),
            'usage:')
        self.assertEqual(
            mouth.get(),
            'help <command>')

        self.assertEqual(mouth.get(), 'Shelly version *unknown*')

        self.assertEqual(mouth.get(),
                         "Sorry, I do not know how to handle 'unknownCommand'")

        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        with self.assertRaises(Exception):
            inbox.get_nowait()

if __name__ == '__main__':

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

    sys.exit(unittest.main())
