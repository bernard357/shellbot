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

from shellbot import Context
from shellbot.machines import MachineFactory


class MyChannel(object):
    def __init__(self, is_direct=False, is_group=False):
        self.is_direct = is_direct
        self.is_group = is_group


class MyBot(object):
    def __init__(self, is_direct=False, is_group=False):
        self.channel = MyChannel(is_direct, is_group)


direct_bot = MyBot(is_direct=True, is_group=False)
group_bot = MyBot(is_direct=False, is_group=True)
weird_bot = MyBot(is_direct=False, is_group=False)


class MachineFactoryTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_get_machine_machine(self):

        logging.info("***** get_machine Machine")

        factory = MachineFactory(module='shellbot.machines.base',
                                 name='Machine')
        void_machine = factory.get_machine()
        direct_machine = factory.get_machine(bot=direct_bot)
        group_machine = factory.get_machine(bot=group_bot)
        weird_machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_input(self):

        logging.info("***** get_machine Input")

        factory = MachineFactory(module='shellbot.machines.input',
                                 question="What's Up, Doc?")
        void_machine = factory.get_machine()
        direct_machine = factory.get_machine(bot=direct_bot)
        group_machine = factory.get_machine(bot=group_bot)
        weird_machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_menu(self):

        logging.info("***** get_machine Menu")

        factory = MachineFactory(module='shellbot.machines.menu',
                                 question="What's Up, Doc?",
                                 options=["option 1", "option 2"])
        void_machine = factory.get_machine()
        direct_machine = factory.get_machine(bot=direct_bot)
        group_machine = factory.get_machine(bot=group_bot)
        weird_machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_sequence(self):

        logging.info("***** get_machine Sequence")

        factory = MachineFactory(module='shellbot.machines.sequence',
                                 machines=[])
        void_machine = factory.get_machine()
        direct_machine = factory.get_machine(bot=direct_bot)
        group_machine = factory.get_machine(bot=group_bot)
        weird_machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_steps(self):

        logging.info("***** get_machine Steps")

        factory = MachineFactory(module='shellbot.machines.steps',
                                 steps=[])
        void_machine = factory.get_machine()
        direct_machine = factory.get_machine(bot=direct_bot)
        group_machine = factory.get_machine(bot=group_bot)
        weird_machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_unknown(self):

        logging.info("***** get_machine invalid machine")

        factory = MachineFactory(module='shellbot.machines.*unknown')
        void_machine = factory.get_machine()
        direct_machine = factory.get_machine(bot=direct_bot)
        group_machine = factory.get_machine(bot=group_bot)
        weird_machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_void(self):

        logging.info("***** get_machine void")

        factory = MachineFactory()

        with self.assertRaises(AssertionError):
            machine = factory.get_machine()
        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=direct_bot)
        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=group_bot)
        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_for_direct_channel(self):

        logging.info("***** get_machine_for_direct_channel")


        class BoringMachine(object):
            type = 'boring'

        class MyFactory(MachineFactory):

            def get_machine_for_direct_channel(self, bot):
                return BoringMachine()

        factory = MyFactory()

        with self.assertRaises(AssertionError):
            machine = factory.get_machine()

        machine = factory.get_machine(bot=direct_bot)
        self.assertTrue(isinstance(machine, BoringMachine))

        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=group_bot)

        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=weird_bot)

    def test_get_machine_for_group_channel(self):

        logging.info("***** get_machine_for_group_channel")


        class BoringMachine(object):
            type = 'boring'

        class MyFactory(MachineFactory):

            def get_machine_for_group_channel(self, bot):
                return BoringMachine()

        factory = MyFactory()

        with self.assertRaises(AssertionError):
            machine = factory.get_machine()

        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=direct_bot)

        machine = factory.get_machine(bot=group_bot)
        self.assertTrue(isinstance(machine, BoringMachine))

        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=weird_bot)

    def test_get_default_machine(self):

        logging.info("***** get_default_machine")


        class BoringMachine(object):
            type = 'boring'

        class MyFactory(MachineFactory):

            def get_default_machine(self, bot):
                return BoringMachine()

        factory = MyFactory()

        machine = factory.get_machine()
        self.assertTrue(isinstance(machine, BoringMachine))

        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=direct_bot)

        with self.assertRaises(AssertionError):
            machine = factory.get_machine(bot=group_bot)

        machine = factory.get_machine(bot=weird_bot)
        self.assertTrue(isinstance(machine, BoringMachine))


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
