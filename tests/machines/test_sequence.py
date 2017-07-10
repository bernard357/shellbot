#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
from threading import Timer
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, Engine, ShellBot
from shellbot.machines import Sequence

my_engine = Engine()
my_bot = ShellBot(engine=my_engine)


class FakeMachine(object):
    def __init__(self):
        self._reset = False

    def reset(self):
        self._reset = True

    def tick(self):
        pass


class SequenceTests(unittest.TestCase):

    def tearDown(self):
        my_engine.context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        self.assertEqual(len(sequence.machines), 3)

    def test_getter(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])

        # undefined key
        self.assertEqual(sequence.get('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(sequence.get('hello', whatever), whatever)

        # set the key
        sequence.set('hello', 'world')
        self.assertEqual(sequence.get('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(sequence.get('hello', 'whatever'), 'world')

        # except when set to None
        sequence.set('special', None)
        self.assertEqual(sequence.get('special', []), [])

    def test_reset(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        sequence.reset()
        self.assertTrue(sequence.machines[0]._reset)
        self.assertTrue(sequence.machines[1]._reset)
        self.assertTrue(sequence.machines[2]._reset)

    def test_start(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        sequence.start()

    def test_tick(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        sequence.tick()

    def test_is_running(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        self.assertFalse(sequence.is_running)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
