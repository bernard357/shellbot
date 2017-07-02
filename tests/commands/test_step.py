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
from shellbot.stores import MemoryStore
from shellbot.commands import Step


my_store = MemoryStore()
my_bot = ShellBot(mouth=Queue(), store=my_store)


class StepTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Step(my_bot)

        self.assertEqual(c.keyword, u'step')
        self.assertEqual(
            c.information_message,
            u'Move process to next step')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Step(my_bot)

        logging.debug("- without machine")
        with self.assertRaises(AttributeError):
            c.execute()

        logging.debug("- with machine")
        my_bot.machine = mock.Mock()
        c.execute()

        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
