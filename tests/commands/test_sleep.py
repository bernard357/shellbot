#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Sleep

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class SleepTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Sleep(my_engine)

        self.assertEqual(c.keyword, u'sleep')
        self.assertEqual(c.information_message, u'Sleep for a while')
        self.assertEqual(c.usage_message, u'sleep <n>')
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Sleep(my_engine)

        c.DEFAULT_DELAY = 0.001
        c.execute(my_bot, u'')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'0.001')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
