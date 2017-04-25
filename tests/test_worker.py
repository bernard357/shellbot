#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import os
import mock
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, Worker

my_bot = ShellBot(inbox=Queue(), mouth=Queue())


class WorkerTests(unittest.TestCase):

    def test_static(self):

        logging.info('*** Static test ***')

        my_bot.context = Context()
        worker = Worker(bot=my_bot)

        worker_process = Process(target=worker.work)
        worker_process.daemon = True
        worker_process.start()

        worker_process.join(1.0)
        if worker_process.is_alive():
            logging.info('Stopping worker')
            my_bot.context.set('general.switch', 'off')
            worker_process.join()

        self.assertFalse(worker_process.is_alive())
        self.assertEqual(my_bot.context.get('worker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        my_bot.inbox.put(('echo', 'hello world'))
        my_bot.inbox.put(('help', 'help'))
        my_bot.inbox.put(('pass', ''))
        my_bot.inbox.put(('sleep', '2'))
        my_bot.inbox.put(('version', ''))
        my_bot.inbox.put(('unknownCommand', ''))
        my_bot.inbox.put(Exception('EOQ'))

        my_bot.context = Context()
        my_bot.shell.load_default_commands()
        worker = Worker(bot=my_bot)
        worker.work()

        self.assertEqual(my_bot.context.get('worker.counter'), 6)

        self.assertEqual(my_bot.mouth.get(), 'hello world')

        self.assertEqual(
            my_bot.mouth.get(),
            u'help - Show commands and usage.\nusage:\nhelp <command>')

        self.assertEqual(my_bot.mouth.get(), u'Shelly version *unknown*')

        self.assertEqual(my_bot.mouth.get(),
                         "Sorry, I do not know how to handle 'None'")

        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        with self.assertRaises(Exception):
            my_bot.inbox.get_nowait()

    def test_work(self):

        logging.info("*** work")

        my_bot.context = Context()
        worker = Worker(bot=my_bot)
        worker.process = mock.Mock(side_effect=Exception('unexpected exception'))
        worker.inbox.put(('do', 'this'))
        worker.work()
        self.assertEqual(worker.context.get('worker.counter'), 1)

        my_bot.context = Context()
        worker = Worker(bot=my_bot)
        worker.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        worker.inbox.put(('do', 'that'))
        worker.work()
        self.assertEqual(worker.context.get('worker.counter'), 1)

    def test_process(self):

        logging.info("*** process")

        my_bot.context = Context()
        my_bot.shell._commands = {}
        worker = Worker(bot=my_bot)
        worker.bot.say = mock.Mock(side_effect=[Exception(), True])
        with self.assertRaises(Exception):
            worker.process(item=('hello', 'here'), counter=1)

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
