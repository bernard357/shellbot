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
        self.assertEqual(my_bot.mouth.get().text,
                         u"Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_fan(self):

        class MyFan(Default):
            def put(self, arguments):
                assert arguments == '*unknown*'

        my_bot.fan = MyFan()

        c = Default(my_bot)

        with mock.patch.object(c,
                               'has_listeners',
                               return_value=True) as mocked:
            c.execute('*unknown*')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
