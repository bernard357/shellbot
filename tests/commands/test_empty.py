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

    def test_empty(self):

        logging.info('***** empty')

        my_bot.shell.load_command('shellbot.commands.help')

        from shellbot.commands import Empty

        c = Empty(my_bot)

        self.assertEqual(c.keyword, u'*empty')
        self.assertEqual(c.information_message, u'Handle empty command')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        c.execute()
        self.assertEqual(
            my_bot.mouth.get(),
            u'Available commands:\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        c = Empty(my_bot)
        c.shell._commands = {}
        c.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'No help command has been found.')
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
