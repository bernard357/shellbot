#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process, Manager
import sys
from threading import Timer
import time

from shellbot import Context, Engine, ShellBot
from shellbot.machines import Sequence


class FakeMachine(object):  # do not change is_running during life cycle

    def __init__(self, bot=None, running=False):
        self.mutables = Manager().dict()
        self.mutables['running'] = running
        self.mutables['reset'] = False
        self.mutables['started'] = False
        self.mutables['stopped'] = False
        self.mutables['ran'] = False

    def reset(self):
        self.mutables['reset'] = True
        if self.is_running:
            return False
        return True

    def start(self):
        self.mutables['started'] = True
        self.run()

    def stop(self):
        self.mutables['stopped'] = True

    def run(self):
        self.mutables['ran'] = True
        while self.is_running and not self.mutables.get('stopped'):
            time.sleep(0.01)

    @property
    def is_running(self):
        return self.mutables['running']


class SequenceTests(unittest.TestCase):

    def setUp(self):
        self.stopped_1 = FakeMachine()
        self.stopped_2 = FakeMachine()
        self.stopped_3 = FakeMachine()
        self.running_1 = FakeMachine(running=True)

    def tearDown(self):
        del self.stopped_1
        del self.stopped_2
        del self.stopped_3
        del self.running_1
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("***** init")

        sequence = Sequence(machines=[self.stopped_1, self.stopped_2, self.stopped_3])
        self.assertEqual(len(sequence.machines), 3)

    def test_getter(self):

        logging.info("***** get and set")

        sequence = Sequence(machines=[self.stopped_1, self.stopped_2, self.stopped_3])

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

        logging.info("***** reset")

        sequence = Sequence(machines=[self.stopped_1, self.stopped_2, self.stopped_3])
        self.assertTrue(sequence.reset())
        self.assertTrue(sequence.machines[0].mutables.get('reset'))
        self.assertTrue(sequence.machines[1].mutables.get('reset'))
        self.assertTrue(sequence.machines[2].mutables.get('reset'))

    def test_start(self):

        logging.info("***** start")

        sequence = Sequence(machines=[self.stopped_1, self.stopped_2, self.stopped_3])
        process = sequence.start()
        process.join()
        self.assertTrue(sequence.machines[0].mutables.get('started'))
        self.assertTrue(sequence.machines[0].mutables.get('ran'))
        self.assertTrue(sequence.machines[1].mutables.get('started'))
        self.assertTrue(sequence.machines[1].mutables.get('ran'))
        self.assertTrue(sequence.machines[2].mutables.get('started'))
        self.assertTrue(sequence.machines[2].mutables.get('ran'))

    def test_stop(self):

        logging.info("***** stop")

        sequence = Sequence(machines=[self.stopped_1, self.running_1, self.stopped_2])
        process = sequence.start()

        while sequence.machines[0].mutables.get('started') != True:
            time.sleep(0.001)
        while sequence.machines[0].mutables.get('ran') != True:
            time.sleep(0.001)
        while sequence.machines[1].mutables.get('started') != True:
            time.sleep(0.001)
        while sequence.machines[1].mutables.get('ran') != True:
            time.sleep(0.001)
        self.assertFalse(sequence.machines[1].mutables.get('stopped'))
        self.assertFalse(sequence.machines[2].mutables.get('started'))
        self.assertFalse(sequence.machines[2].mutables.get('ran'))

        sequence.stop()
        process.join()

        self.assertTrue(sequence.machines[0].mutables.get('started'))
        self.assertTrue(sequence.machines[0].mutables.get('ran'))
        self.assertTrue(sequence.machines[1].mutables.get('started'))
        self.assertTrue(sequence.machines[1].mutables.get('ran'))
        self.assertTrue(sequence.machines[1].mutables.get('stopped'))
        self.assertFalse(sequence.machines[2].mutables.get('started'))
        self.assertFalse(sequence.machines[2].mutables.get('ran'))

    def test_run(self):

        logging.info("***** run")

        sequence = Sequence(machines=[self.stopped_1, self.stopped_2, self.stopped_3])
        sequence.run()
        self.assertTrue(sequence.machines[0].mutables.get('started'))
        self.assertTrue(sequence.machines[0].mutables.get('ran'))
        self.assertTrue(sequence.machines[1].mutables.get('started'))
        self.assertTrue(sequence.machines[1].mutables.get('ran'))
        self.assertTrue(sequence.machines[2].mutables.get('started'))
        self.assertTrue(sequence.machines[2].mutables.get('ran'))

    def test_is_running(self):

        logging.info("***** is_running")

        sequence = Sequence(machines=[self.stopped_1, self.stopped_2, self.stopped_3])
        self.assertFalse(sequence.is_running)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
