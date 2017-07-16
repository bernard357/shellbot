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
from shellbot.commands import Step


my_store = MemoryStore()
my_engine = Engine(mouth=Queue(), store=my_store)
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)



class StepTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Step(my_engine)

        self.assertEqual(c.keyword, u'step')
        self.assertEqual(
            c.information_message,
            u'Move process to next step')
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Step(my_engine)

        logging.debug("- without machine")
        with self.assertRaises(AttributeError):
            c.execute(my_bot)

        logging.debug("- with machine")
        my_bot.machine = mock.Mock()
        c.execute(my_bot)

        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
