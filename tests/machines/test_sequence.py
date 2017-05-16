#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
import os
from multiprocessing import Process
import sys
from threading import Timer
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot
from shellbot.machines import Sequence


class FakeMachine(object):
    def tick(self):
        pass


class SequenceTests(unittest.TestCase):

    def test_init(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        self.assertEqual(len(sequence.machines), 3)

    def test_start(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        sequence.start()

    def test_tick(self):

        sequence = Sequence([FakeMachine(), FakeMachine(), FakeMachine()])
        sequence.tick()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
