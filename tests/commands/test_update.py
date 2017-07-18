#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.stores import MemoryStore
from shellbot.commands import Update


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


class UpdateTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context,
                             mouth=Queue())
        self.store = MemoryStore(context=self.context)
        self.bot = Bot(engine=self.engine)

    def tearDown(self):
        del self.bot
        del self.store
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        c = Update(self.engine)

        self.assertEqual(c.keyword, u'update')
        self.assertEqual(
            c.information_message,
            u'Update input content')
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Update(self.engine)
        c.execute(self.bot, u'')
        self.assertEqual(
            self.engine.mouth.get().text,
            u'Thanks to provide the key and the data')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, u'description')
        self.assertEqual(
            self.engine.mouth.get().text,
            u'There is nothing to update, input is empty')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        self.bot.update('update', 'PO', '1234A')
        c.execute(self.bot, u'description')
        self.assertEqual(
            self.engine.mouth.get().text,
            u'Thanks to provide the key and the data')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
