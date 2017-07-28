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
from shellbot.commands import Command, Help


class MyChannel(object):
    is_direct = False


class MyBot(object):
    channel = MyChannel()

    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_engine = Engine(mouth=Queue())
my_bot = MyBot(engine=my_engine)


class HelpTests(unittest.TestCase):

    def setUp(self):
        my_engine.shell = Shell(engine=my_engine)

    def tearDown(self):
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        c = Help(my_engine)

        self.assertEqual(c.keyword, u'help')
        self.assertEqual(
            c.information_message,
            u'Show commands and usage')
        self.assertEqual(c.usage_message, u'help <command>')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

    def test_execute_no_usage(self):

        logging.info('***** execute/no_usage')

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

    def test_in_direct_or_in_group(self):

        logging.info('***** in_direct or in_group')

        c = Help(my_engine)

        my_engine.load_command('shellbot.commands.help')

        from shellbot.commands.base import Command

        class Custom(Command):
            keyword =  'custom'
            def execute(self, bot, arguments):
                bot.say("{}, really?".format(arguments))

        my_engine.load_command(Custom(my_engine))

        my_bot.channel.is_direct = False  # group channel

        my_engine.shell.command('custom').in_direct = False
        my_engine.shell.command('custom').in_group = False
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'This command is unknown.')

        my_engine.shell.command('custom').in_direct = True
        my_engine.shell.command('custom').in_group = False
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'This command is unknown.')

        my_engine.shell.command('custom').in_direct = False
        my_engine.shell.command('custom').in_group = True
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'custom - None\nusage: custom')

        my_engine.shell.command('custom').in_direct = True
        my_engine.shell.command('custom').in_group = True
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'custom - None\nusage: custom')

        my_bot.channel.is_direct = True  # direct channel

        my_engine.shell.command('custom').in_direct = False
        my_engine.shell.command('custom').in_group = False
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'This command is unknown.')

        my_engine.shell.command('custom').in_direct = True
        my_engine.shell.command('custom').in_group = False
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'custom - None\nusage: custom')

        my_engine.shell.command('custom').in_direct = False
        my_engine.shell.command('custom').in_group = True
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'This command is unknown.')

        my_engine.shell.command('custom').in_direct = True
        my_engine.shell.command('custom').in_group = True
        c.execute(my_bot, "custom")
        self.assertEqual(
            my_engine.mouth.get().text,
            u'custom - None\nusage: custom')

        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
