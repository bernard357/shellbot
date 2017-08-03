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
from shellbot.commands import Start


class MyMachine(object):
    def __init__(self):
        self.restarted = False

    def restart(self, **kwargs):
        self.parameters = kwargs
        return self.restarted


class MyBot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


class StartTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context,
                             mouth=Queue())
        self.space = LocalSpace(context=self.context, ears=self.engine.ears)
        self.store = MemoryStore(context=self.context)
        self.machine = MyMachine()
        self.bot = MyBot(engine=self.engine)
        self.bot.machine = None

    def tearDown(self):
        del self.bot
        del self.machine
        del self.store
        del self.space
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        c = Start(self.engine)

        self.assertEqual(c.keyword, u'start')
        self.assertEqual(
            c.information_message,
            u"Start a new sequence")
        self.assertFalse(c.is_hidden)
        self.assertTrue(c.in_direct)
        self.assertFalse(c.in_group)

        c = Start(self.engine, in_group=True)
        self.assertTrue(c.in_group)

    def test_execute(self):

        logging.info('***** execute')

        c = Start(self.engine)

        logging.debug("- without machine")
        c.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u"No state machine is available")

        logging.debug("- with machine - not restarted")
        self.bot.machine = self.machine
        c.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u"Cannot restart the state machine")

        logging.debug("- with machine - restarted")
        self.bot.machine.restarted = True
        c.execute(self.bot)
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        logging.debug("- with parameters")
        self.bot.machine.restarted = True
        c.execute(self.bot,
                  arguments='again',
                  attachment='file.log',
                  url='http://here/you/go')
        self.assertEqual(self.machine.parameters,
                         {'arguments': 'again',
                          'attachment': 'file.log',
                          'url': 'http://here/you/go'})
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
