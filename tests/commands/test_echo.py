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
from shellbot.commands import Echo


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class EchoTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Echo(my_bot)

        self.assertEqual(c.keyword, u'echo')
        self.assertEqual(c.information_message, u'Echo input string')
        self.assertEqual(c.usage_message, u'echo "a string to be echoed"')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Echo(my_bot)

        message = u"hello world"
        c.execute(message)
        self.assertEqual(my_bot.mouth.get().text, message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
