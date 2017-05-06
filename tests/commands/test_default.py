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
from shellbot.commands import Default


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class DefaultTests(unittest.TestCase):

    def test_init(self):

        c = Default(my_bot)

        self.assertEqual(c.keyword, u'*default')
        self.assertEqual(c.information_message, u'Handle unmatched command')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        c = Default(my_bot)

        c.execute('*unknown*')
        self.assertEqual(my_bot.mouth.get(),
                         u"Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_call_once(self):

        c = Default(my_bot)
        self.assertTrue(c._call_once is None)

        mocked = mock.Mock()

        c.call_once(mocked)
        c.execute('answer 1')
        mocked.assert_called_with('answer 1')
        self.assertTrue(c._call_once is None)

        c.call_once(mocked)
        c.execute('answer 2')
        mocked.assert_called_with('answer 2')
        self.assertTrue(c._call_once is None)

        c.call_once(mocked)
        with self.assertRaises(AssertionError):
            c.call_once(mocked)

        c.call_once(None)
        c.call_once(mocked)

    def test_callback(self):

        c = Default(my_bot)
        self.assertTrue(c._callback is None)

        mocked = mock.Mock()
        c.callback(mocked)

        c.execute('*unknown*')
        mocked.assert_called_with('*unknown*')
        self.assertTrue(c._callback is not None)

        with self.assertRaises(AssertionError):
            c.callback(mocked)

        c.callback(None)
        c.callback(mocked)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
