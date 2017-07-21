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
from shellbot.spaces import LocalSpace
from shellbot.stores import MemoryStore
from shellbot.commands import Step


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))

class StepTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context,
                             mouth=Queue())
        self.space = LocalSpace(context=self.context, ears=self.engine.ears)
        self.store = MemoryStore(context=self.context)
        self.bot = Bot(engine=self.engine)

    def tearDown(self):
        del self.bot
        del self.store
        del self.space
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        c = Step(self.engine)

        self.assertEqual(c.keyword, u'step')
        self.assertEqual(
            c.information_message,
            u'Move process to next step')
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Step(self.engine)

        logging.debug("- without machine")
        with self.assertRaises(AttributeError):
            c.execute(self.bot)

        logging.debug("- with machine")
        self.bot.machine = mock.Mock()
        c.execute(self.bot)

        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
