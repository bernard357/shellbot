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
from shellbot.commands import Update


my_store = MemoryStore()
my_bot = ShellBot(mouth=Queue(), store=my_store)


class UpdateTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Update(my_bot)

        self.assertEqual(c.keyword, u'update')
        self.assertEqual(
            c.information_message,
            u'Update input content')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Update(my_bot)
        c.execute(u'')
        self.assertEqual(
            my_bot.mouth.get().text,
            u'Thanks to provide the key and the data')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        my_bot.update('update', 'PO', '1234A')
        c.execute(u'description')
        self.assertEqual(
            my_bot.mouth.get().text,
            u'There is nothing to update, input is empty')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
