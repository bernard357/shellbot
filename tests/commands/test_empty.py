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
from shellbot.commands import Empty


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class EmptyTests(unittest.TestCase):


    def test_init(self):

        logging.info('***** init')

        c = Empty(my_bot)

        self.assertEqual(c.keyword, u'*empty')
        self.assertEqual(c.information_message, u'Handle empty command')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        my_bot.shell.load_command('shellbot.commands.help')

        c = Empty(my_bot)

        c.execute()
        self.assertEqual(
            my_bot.mouth.get().text,
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        c = Empty(my_bot)
        my_bot.shell._commands = {}
        c.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'No help command has been found.')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
