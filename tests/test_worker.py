#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Engine, Worker, Vibes

class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("injecting test bot")
        return my_bot


my_engine = MyEngine(inbox=Queue(), mouth=Queue())


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class WorkerTests(unittest.TestCase):

    def tearDown(self):
        my_engine.context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        worker = Worker(engine=my_engine)

        worker_process = worker.start()

        worker_process.join(0.01)
        if worker_process.is_alive():
            logging.info('Stopping worker')
            my_engine.set('general.switch', 'off')
            worker_process.join()

        self.assertFalse(worker_process.is_alive())
        self.assertEqual(my_engine.get('worker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        my_engine.inbox.put(('echo', 'hello world', '*id'))
        my_engine.inbox.put(('help', 'help', '*id'))
        my_engine.inbox.put(('pass', '', '*id'))
        my_engine.inbox.put(('sleep', '0.001', '*id'))
        my_engine.inbox.put(('version', '', '*id'))
        my_engine.inbox.put(('unknownCommand', '', '*id'))
        my_engine.inbox.put(None)

        my_engine.shell.load_default_commands()
        worker = Worker(engine=my_engine)
        worker.run()

        self.assertEqual(
            my_engine.get('worker.counter'), 6)

        self.assertEqual(
            my_engine.mouth.get().text, 'hello world')

        self.assertEqual(
            my_engine.mouth.get().text,
            u'help - Show commands and usage\nusage: help <command>')

        self.assertEqual(
            my_engine.mouth.get().text, u'Shelly version *unknown*')

        self.assertEqual(
            my_engine.mouth.get().text,
            "Sorry, I do not know how to handle 'unknownCommand'")

        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

        with self.assertRaises(Exception):
            my_engine.inbox.get_nowait()

    def test_run(self):

        logging.info("*** run")

        worker = Worker(engine=my_engine)
        worker.process = mock.Mock(side_effect=Exception('TEST'))
        my_engine.inbox.put(('do', 'this', '*id'))
        my_engine.inbox.put(None)
        worker.run()
        self.assertEqual(my_engine.get('worker.counter'), 0)

        my_engine.context.clear()
        worker = Worker(engine=my_engine)
        worker.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        my_engine.inbox.put(('do', 'that', '*id'))
        worker.run()
        self.assertEqual(my_engine.get('worker.counter'), 0)

    def test_process(self):

        logging.info("*** process")

        my_engine.shell._commands = {}
        worker = Worker(engine=my_engine)
        with mock.patch.object(my_bot,
                               'say',
                               side_effect=[Exception(), True]) as mocked:

            with self.assertRaises(Exception):
                worker.process(item=('hello', 'here', '*id'))


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
