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
from shellbot.commands import Default


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class DefaultTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Default(my_bot)

        self.assertEqual(c.keyword, u'*default')
        self.assertEqual(c.information_message, u'Handle unmatched command')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Default(my_bot)

        my_bot.shell.verb = u'*unknown*'
        c.execute('test of default command')
        self.assertEqual(my_bot.mouth.get(),
                         u"Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
