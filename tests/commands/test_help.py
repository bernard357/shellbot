#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, Shell


my_bot = ShellBot(mouth=Queue())

class CommandsTests(unittest.TestCase):

    def setUp(self):
        my_bot.shell = Shell(bot=my_bot)

    def test_help(self):

        logging.info('***** help')

        from shellbot.commands import Help

        c = Help(my_bot)

        self.assertEqual(c.keyword, u'help')
        self.assertEqual(
            c.information_message,
            u'Show commands and usage')
        self.assertEqual(c.usage_message, u'help <command>')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(my_bot.mouth.get(), u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

    def test_help_true(self):

        logging.info('***** help/true')

        my_bot.shell.load_command('shellbot.commands.help')

        from shellbot.commands import Help

        c = Help(my_bot)

        c.execute()
        self.assertEqual(
            my_bot.mouth.get(),
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute("help")
        self.assertEqual(
            my_bot.mouth.get(),
            u'help - Show commands and usage\nusage: help <command>')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_help_false(self):

        logging.info('***** help/false')

        from shellbot.commands import Help

        c = Help(my_bot)

        c.execute()
        self.assertEqual(my_bot.mouth.get(), u'No command has been found.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u"*unknown*command*")
        self.assertEqual(my_bot.mouth.get(), u'No command has been found.')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        my_bot.load_command('shellbot.commands.help')

        c.execute("*unknown*command*")
        self.assertEqual(my_bot.mouth.get(), u'This command is unknown.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
