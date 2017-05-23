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
from shellbot.commands import Close


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class CloseTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Close(my_bot)

        self.assertEqual(c.keyword, u'close')
        self.assertEqual(c.information_message, u'Close this room')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        my_bot.stop = mock.Mock()
        my_bot.dispose = mock.Mock()

        c = Close(my_bot)

        c.execute()
        self.assertEqual(my_bot.mouth.get().text, u'Close this room')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        self.assertTrue(my_bot.stop.called)
        self.assertTrue(my_bot.dispose.called)

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
