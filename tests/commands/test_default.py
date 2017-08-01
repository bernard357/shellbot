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
from shellbot.commands import Default


class Bot(object):
    def __init__(self, engine):
        self.engine = engine
        self.participants = None

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))

    def add_participants(self, persons):
        self.participants = persons


class DefaultTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context, mouth=Queue())
        self.engine.configure()
        self.bot = Bot(engine=self.engine)

    def tearDown(self):
        del self.bot
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("***** init")

        c = Default(self.engine)

        self.assertEqual(c.keyword, u'*default')
        self.assertEqual(c.information_message, u'Handle unmatched command')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_hidden)

    def test_execute_unknown(self):

        logging.info("***** execute unknown")

        c = Default(self.engine)

        c.execute(self.bot, '*unknown*')
        self.assertEqual(self.engine.mouth.get().text,
                         u"Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_execute_named_list(self):

        logging.info("***** execute named list")

        self.engine.configure_from_path(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            + '/test_settings/regular.yaml')

        c = Default(self.engine)

        c.execute(self.bot, 'The Famous Four')
        self.assertEqual(self.engine.mouth.get().text,
                         u"Sorry, I do not know how to handle 'The Famous Four'")
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, 'SupportTeam')
        self.assertEqual(self.engine.mouth.get().text,
                         u"Adding participants from 'SupportTeam'")
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()
        self.assertEqual(self.bot.participants, ['service.desk@acme.com', 'supervisor@brother.mil'])


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
