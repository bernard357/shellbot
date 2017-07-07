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
from shellbot.commands import Empty

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class EmptyTests(unittest.TestCase):


    def test_init(self):

        logging.info('***** init')

        c = Empty(my_engine)

        self.assertEqual(c.keyword, u'*empty')
        self.assertEqual(c.information_message, u'Handle empty command')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        my_engine.shell.load_command('shellbot.commands.help')

        c = Empty(my_engine)

        c.execute(my_bot)
        self.assertEqual(
            my_engine.mouth.get().text,
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

        c = Empty(my_engine)
        my_engine.shell._commands = {}
        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'No help command has been found.')
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
