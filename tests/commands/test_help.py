#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.commands import Command, Help


my_bot = ShellBot(mouth=Queue())


class HelpTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        my_bot.shell = Shell(bot=my_bot)
        c = Help(my_bot)

        self.assertEqual(c.keyword, u'help')
        self.assertEqual(
            c.information_message,
            u'Show commands and usage')
        self.assertEqual(c.usage_message, u'help <command>')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(my_bot.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

    def test_execute_no_usage(self):

        logging.info('***** execute/no_usage')

        my_bot.shell = Shell(bot=my_bot)

        my_bot.shell.load_command(Command(keyword='hello',
                                          information_message='world'))

        c = Help(my_bot)

        c.execute()
        self.assertEqual(
            my_bot.mouth.get().text,
            u'Available commands:\nhello - world')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute('hello')
        self.assertEqual(
            my_bot.mouth.get().text,
            u'hello - world\nusage: hello')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute('*unknown*')
        self.assertEqual(
            my_bot.mouth.get().text,
            u'This command is unknown.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_help_true(self):

        logging.info('***** help/true')

        my_bot.shell = Shell(bot=my_bot)
        my_bot.shell.load_command('shellbot.commands.help')

        c = Help(my_bot)

        c.execute()
        self.assertEqual(
            my_bot.mouth.get().text,
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute("help")
        self.assertEqual(
            my_bot.mouth.get().text,
            u'help - Show commands and usage\nusage: help <command>')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_help_false(self):

        logging.info('***** help/false')

        my_bot.shell = Shell(bot=my_bot)
        c = Help(my_bot)

        c.execute()
        self.assertEqual(my_bot.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u"*unknown*command*")
        self.assertEqual(my_bot.mouth.get().text, u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        my_bot.load_command('shellbot.commands.help')

        c.execute("*unknown*command*")
        self.assertEqual(my_bot.mouth.get().text, u'This command is unknown.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
