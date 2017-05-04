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

class CommandTests(unittest.TestCase):

    def setUp(self):
        my_bot.shell = Shell(bot=my_bot)

    def test_version(self):

        logging.info('***** version')

        my_bot.shell.configure(settings={
            'bot': {'name': 'testy', 'version': '17.4.1'},
        })

        from shellbot.commands import Version

        c = Version(my_bot)

        self.assertEqual(c.keyword, u'version')
        self.assertEqual(c.information_message, u'Display software version')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        c.execute()
        self.assertEqual(my_bot.mouth.get(), 'testy version 17.4.1')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
