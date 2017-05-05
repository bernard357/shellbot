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
from shellbot.commands import Noop


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class NoopTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Noop(my_bot)

        self.assertEqual(c.keyword, u'pass')
        self.assertEqual(c.information_message, u'Do absolutely nothing')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Noop(my_bot)

        c.execute()
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
