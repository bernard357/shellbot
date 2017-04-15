#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorlog
import unittest
import logging
import os
from multiprocessing import Process, Queue
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Shell, Worker


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
            'help - Show commands and usage.')
        self.assertEqual(
            mouth.get(),
            'usage:')
        self.assertEqual(
            mouth.get(),
            'help <command>')

        self.assertEqual(mouth.get(), 'Shelly version *unknown*')

        self.assertEqual(mouth.get(),
                         "Sorry, I do not know how to handle 'None'")

        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        with self.assertRaises(Exception):
            inbox.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
