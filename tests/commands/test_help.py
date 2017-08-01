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


class HelpTests(unittest.TestCase):

    def setUp(self):
        self.engine = Engine(mouth=Queue())
        self.engine.configure()
        self.engine.shell = Shell(engine=self.engine)
        self.bot = MyBot(engine=self.engine)

    def tearDown(self):
        del self.bot
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        c = Help(self.engine)

        self.assertEqual(c.keyword, u'help')
        self.assertEqual(
            c.information_message,
            u'Show commands and usage')
        self.assertEqual(c.usage_message, u'help <command>')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(self.engine.mouth.get_nowait())

    def test_execute_no_usage(self):

        logging.info('***** execute/no_usage')

        self.engine.shell.load_command(Command(keyword='hello',
                                               information_message='world'))

        c = Help(self.engine)

        c.execute(self.bot)
        self.assertEqual(
            self.engine.mouth.get().text,
            u'Available commands:\nhello - world')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, 'hello')
        self.assertEqual(
            self.engine.mouth.get().text,
            u'hello - world\nusage: hello')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, '*unknown*')
        self.assertEqual(
            self.engine.mouth.get().text,
            u'This command is unknown.')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_help_true(self):

        logging.info('***** help/true')

        self.engine.shell.load_command('shellbot.commands.help')

        c = Help(self.engine)

        c.execute(self.bot)
        self.assertEqual(
            self.engine.mouth.get().text,
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, "help")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'help - Show commands and usage\nusage: help <command>')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_help_false(self):

        logging.info('***** help/false')

        c = Help(self.engine)

        c.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, u"*unknown*command*")
        self.assertEqual(self.engine.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(self.engine.mouth.get_nowait())

        self.engine.load_command('shellbot.commands.help')

        c.execute(self.bot, "*unknown*command*")
        self.assertEqual(self.engine.mouth.get().text, u'This command is unknown.')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_in_direct_or_in_group(self):

        logging.info('***** in_direct or in_group')

        c = Help(self.engine)

        self.engine.load_command('shellbot.commands.help')

        from shellbot.commands.base import Command

        class Custom(Command):
            keyword =  'custom'
            def execute(self, bot, arguments=None, **kwargs):
                bot.say("{}, really?".format(arguments))

        self.engine.load_command(Custom(self.engine))

        self.bot.channel.is_direct = False  # group channel

        self.engine.shell.command('custom').in_direct = False
        self.engine.shell.command('custom').in_group = False
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'This command is unknown.')

        self.engine.shell.command('custom').in_direct = True
        self.engine.shell.command('custom').in_group = False
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'This command is unknown.')

        self.engine.shell.command('custom').in_direct = False
        self.engine.shell.command('custom').in_group = True
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'custom - None\nusage: custom')

        self.engine.shell.command('custom').in_direct = True
        self.engine.shell.command('custom').in_group = True
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'custom - None\nusage: custom')

        self.bot.channel.is_direct = True  # direct channel

        self.engine.shell.command('custom').in_direct = False
        self.engine.shell.command('custom').in_group = False
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'This command is unknown.')

        self.engine.shell.command('custom').in_direct = True
        self.engine.shell.command('custom').in_group = False
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'custom - None\nusage: custom')

        self.engine.shell.command('custom').in_direct = False
        self.engine.shell.command('custom').in_group = True
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'This command is unknown.')

        self.engine.shell.command('custom').in_direct = True
        self.engine.shell.command('custom').in_group = True
        c.execute(self.bot, "custom")
        self.assertEqual(
            self.engine.mouth.get().text,
            u'custom - None\nusage: custom')

        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_named_lists(self):

        logging.info('***** named lists')

        c = Help(self.engine)

        self.engine.configure_from_path(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            + '/test_settings/regular.yaml')

        self.engine.shell = Shell(engine=self.engine)
        self.engine.load_command('shellbot.commands.help')

        c.execute(self.bot)

        self.assertEqual(
            self.engine.mouth.get().text,
            u"Available commands:\nhelp - Show commands and usage\nSupportTeam - add participants (service.desk@acme.com, ...)")

        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
