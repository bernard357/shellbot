#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.machines import MachinesFactory


my_context = Context()

class MachinesFactoryTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_get_machine(self):

        logging.info("***** get Machine")

        factory = MachinesFactory(module='shellbot.machines.base',
                                  name='Machine')
        machine = factory.get_machine()

    def test_get_input(self):

        logging.info("***** get Input")

        factory = MachinesFactory(module='shellbot.machines.input',
                                  question="What's Up, Doc?")
        machine = factory.get_machine()

    def test_get_menu(self):

        logging.info("***** get Menu")

        factory = MachinesFactory(module='shellbot.machines.menu',
                                  question="What's Up, Doc?",
                                  options=["option 1", "option 2"])
        machine = factory.get_machine()

    def test_get_sequence(self):

        logging.info("***** get Sequence")

        factory = MachinesFactory(module='shellbot.machines.sequence',
                                  machines=[])
        machine = factory.get_machine()

    def test_get_steps(self):

        logging.info("***** get Steps")

        factory = MachinesFactory(module='shellbot.machines.steps',
                                  steps=[])
        machine = factory.get_machine()

    def test_get_unknown(self):

        logging.info("***** get invalid machine")

        factory = MachinesFactory(module='shellbot.machines.*unknown')
        machine = factory.get_machine()

    def test_get_void(self):

        logging.info("***** get void")

        factory = MachinesFactory()

        with self.assertRaises(AssertionError):
            machine = factory.get_machine()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
