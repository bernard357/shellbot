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

    def test_close(self):

        logging.info('***** close')

        my_bot.stop = mock.Mock()
        my_bot.dispose = mock.Mock()

        from shellbot.commands import Close

        c = Close(my_bot)

        self.assertEqual(c.keyword, u'close')
        self.assertEqual(c.information_message, u'Close this room')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(my_bot.mouth.get(), u'Close this room')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()
        self.assertTrue(my_bot.stop.called)
        self.assertTrue(my_bot.dispose.called)

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
