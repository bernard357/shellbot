#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Command, Help

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class HelpTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        my_bot.shell = Shell(engine=my_engine)
        c = Help(my_engine)

        self.assertEqual(c.keyword, u'help')
        self.assertEqual(
            c.information_message,
            u'Show commands and usage')
        self.assertEqual(c.usage_message, u'help <command>')
        self.assertFalse(c.is_hidden)

        my_bot.shell = Shell(engine=my_engine)

        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

    def test_execute_no_usage(self):

        logging.info('***** execute/no_usage')

        my_engine.shell = Shell(engine=my_engine)

        my_engine.shell.load_command(Command(keyword='hello',
                                             information_message='world'))

        c = Help(my_engine)

        c.execute(my_bot)
        self.assertEqual(
            my_engine.mouth.get().text,
            u'Available commands:\nhello - world')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, 'hello')
        self.assertEqual(
            my_engine.mouth.get().text,
            u'hello - world\nusage: hello')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, '*unknown*')
        self.assertEqual(
            my_engine.mouth.get().text,
            u'This command is unknown.')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_help_true(self):

        logging.info('***** help/true')

        my_engine.shell = Shell(engine=my_engine)
        my_engine.shell.load_command('shellbot.commands.help')

        c = Help(my_engine)

        c.execute(my_bot)
        self.assertEqual(
            my_engine.mouth.get().text,
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, "help")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'help - Show commands and usage\nusage: help <command>')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_help_false(self):

        logging.info('***** help/false')

        my_engine.shell = Shell(engine=my_engine)
        c = Help(my_engine)

        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u"*unknown*command*")
        self.assertEqual(my_engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

        my_engine.load_command('shellbot.commands.help')

        c.execute(my_bot, "*unknown*command*")
        self.assertEqual(my_engine.mouth.get().text, u'This command is unknown.')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
