#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import json
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.events import Message
from shellbot.updaters import Updater

my_bot = ShellBot()


class BaseTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        u = Updater()
        self.assertEqual(u.bot, None)

    def test_on_init(self):

        logging.info('***** on_init')

        class MyUpdater(Updater):

            def on_init(self, more=None, **kwargs):
                self.more = more

        u = MyUpdater(more='more', weird='weird')
        self.assertEqual(u.more, 'more')
        with self.assertRaises(AttributeError):
            self.assertEqual(u.weird, 'weird')

    def test_on_bond(self):

        logging.info('***** on_bond')

        u = Updater()
        u.on_bond()

        class MyUpdater(Updater):

            def on_init(self, **kwargs):
                self.count = 0

            def on_bond(self):
                self.count += 1

        u = MyUpdater(bot=my_bot)
        self.assertEqual(u.count, 0)
        my_bot.dispatch('bond')
        self.assertEqual(u.count, 1)

    def test_on_dispose(self):

        logging.info('***** on_dispose')

        u = Updater()
        u.on_dispose()

        class MyUpdater(Updater):

            def on_init(self, **kwargs):
                self.count = 0

            def on_dispose(self):
                self.count += 1

        u = MyUpdater(bot=my_bot)
        self.assertEqual(u.count, 0)
        my_bot.dispatch('dispose')
        self.assertEqual(u.count, 1)


    def test_filter(self):

        logging.info('***** filter')

        u = Updater()
        u.put = mock.Mock()
        message = Message({
            'personEmail': 'alice@acme.com',
            'text': 'my message',
        })

        outcome = u.filter(message)
        self.assertEqual(outcome.attributes, message.attributes)
        u.put.assert_called_with(message)

    def test_put(self):

        logging.info('***** put')

        u = Updater()
        message = Message({
            'personEmail': 'alice@acme.com',
            'text': 'my message',
        })

        with mock.patch('sys.stdout') as mocked:
            u.put(message)
            mocked.write.assert_called_with('{"personEmail": "alice@acme.com", "text": "my message", "type": "message"}\n')

    def test_format(self):

        logging.info('***** format')

        u = Updater()

        inbound = 'hello world'
        outbound = u.format(inbound)
        self.assertEqual(outbound, inbound)

        inbound = Message({'text': 'hello world'})
        outbound = u.format(inbound)
        self.assertEqual(json.loads(outbound),
                         {"text": "hello world", "type": "message"})

        inbound = Message({'personEmail': 'a@me.com'})
        outbound = u.format(inbound)
        self.assertEqual(json.loads(outbound),
                         {"type": "message", "personEmail": "a@me.com"})

        inbound = Message({'text': 'hello world', 'personEmail': 'a@me.com'})
        outbound = u.format(inbound)
        self.assertEqual(json.loads(outbound),
                         {"text": "hello world", "type": "message", "personEmail": "a@me.com"})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
