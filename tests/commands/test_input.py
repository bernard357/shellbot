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
from shellbot.commands import Input


my_store = MemoryStore()
my_bot = ShellBot(mouth=Queue(), store=my_store)


class InputTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Input(my_bot)

        self.assertEqual(c.keyword, u'input')
        self.assertEqual(
            c.information_message,
            u'Display all input')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Input(my_bot)

        c.execute()
        self.assertEqual(
            my_bot.mouth.get().text,
            u'There is nothing to display')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        my_bot.update('input', 'PO#', '1234A')
        my_bot.update('input', 'description', 'part does not fit')
        c.execute()
        self.assertEqual(
            my_bot.mouth.get().text,
            u'Input:\nPO# - 1234A\ndescription - part does not fit')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
