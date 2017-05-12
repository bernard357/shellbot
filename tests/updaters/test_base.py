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
from shellbot.updaters import Updater


class BaseTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        u = Updater(bot='b')
        self.assertEqual(u.bot, 'b')

    def test_from_base(self):

        logging.info('***** from base')

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
        message = {
            'personEmail': 'alice@acme.com',
            'text': 'my message',
        }

        with mock.patch('sys.stdout') as mocked:
            u.put(message)
            mocked.write.assert_called_with('alice@acme.com: my message\n')

    def test_format(self):

        logging.info('***** format')

        u = Updater(bot='b')

        inbound = 'hello world'
        with self.assertRaises(Exception):
            outbound = u.format(message=inbound)

        inbound = {'text': 'hello world'}
        with self.assertRaises(Exception):
            outbound = u.format(message=inbound)

        inbound = {'personEmail': 'a@me.com'}
        with self.assertRaises(Exception):
            outbound = u.format(message=inbound)

        inbound = {'text': 'hello world', 'personEmail': 'a@me.com'}
        outbound = u.format(message=inbound)
        self.assertEqual(outbound, u'a@me.com: hello world')

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
