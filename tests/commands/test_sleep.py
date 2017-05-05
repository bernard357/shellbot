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
from shellbot.commands import Sleep


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class SleepTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Sleep(my_bot)

        self.assertEqual(c.keyword, u'sleep')
        self.assertEqual(c.information_message, u'Sleep for a while')
        self.assertEqual(c.usage_message, u'sleep <n>')
        self.assertFalse(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Sleep(my_bot)

        c.DEFAULT_DELAY = 0.001
        c.execute(u'')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'0.001')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
