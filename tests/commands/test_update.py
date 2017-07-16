#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, Engine, Shell, Vibes
from shellbot.stores import MemoryStore
from shellbot.commands import Update

my_store = MemoryStore()
my_engine = Engine(mouth=Queue(), store=my_store)
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine
        self.data = {}

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))

    def update(self, label, key, value):
        self.data[key] = value

    def recall(self, label):
        return self.data


my_bot = Bot(engine=my_engine)


class UpdateTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Update(my_engine)

        self.assertEqual(c.keyword, u'update')
        self.assertEqual(
            c.information_message,
            u'Update input content')
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Update(my_engine)
        c.execute(my_bot, u'')
        self.assertEqual(
            my_engine.mouth.get().text,
            u'Thanks to provide the key and the data')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'description')
        self.assertEqual(
            my_engine.mouth.get().text,
            u'There is nothing to update, input is empty')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        my_bot.update('update', 'PO', '1234A')
        c.execute(my_bot, u'description')
        self.assertEqual(
            my_engine.mouth.get().text,
            u'Thanks to provide the key and the data')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
