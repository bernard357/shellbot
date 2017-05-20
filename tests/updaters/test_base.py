#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.events import Message
from shellbot.updaters import Updater


class BaseTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        u = Updater(bot='b')
        self.assertEqual(u.bot, 'b')

    def test_on_init(self):

        logging.info('***** on_init')

        class MyUpdater(Updater):

            def on_init(self, more=None, **kwargs):
                self.more = more

        u = MyUpdater(bot='b', more='more', weird='weird')
        self.assertEqual(u.bot, 'b')
        self.assertEqual(u.more, 'more')
        with self.assertRaises(AttributeError):
            self.assertEqual(u.weird, 'weird')

    def test_put(self):

        logging.info('***** put')

        u = Updater(bot='b')
        message = Message({
            'personEmail': 'alice@acme.com',
            'text': 'my message',
        })

        with mock.patch('sys.stdout') as mocked:
            u.put(message)
            mocked.write.assert_called_with('{"text": "my message", "type": "message", "personEmail": "alice@acme.com"}\n')

    def test_format(self):

        logging.info('***** format')

        u = Updater(bot='b')

        inbound = 'hello world'
        outbound = u.format(inbound)
        self.assertEqual(outbound, inbound)

        inbound = Message({'text': 'hello world'})
        outbound = u.format(inbound)
        self.assertEqual(outbound, '{"text": "hello world", "type": "message"}')

        inbound = Message({'personEmail': 'a@me.com'})
        outbound = u.format(inbound)
        self.assertEqual(outbound, '{"type": "message", "personEmail": "a@me.com"}')

        inbound = Message({'text': 'hello world', 'personEmail': 'a@me.com'})
        outbound = u.format(inbound)
        self.assertEqual(outbound, '{"text": "hello world", "type": "message", "personEmail": "a@me.com"}')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
