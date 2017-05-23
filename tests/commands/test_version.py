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
from shellbot.commands import Version


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class VersionTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Version(my_bot)

        self.assertEqual(c.keyword, u'version')
        self.assertEqual(c.information_message, u'Display software version')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        my_bot.shell.configure(settings={
            'bot': {'name': 'testy', 'version': '17.4.1'},
        })

        c = Version(my_bot)

        c.execute()
        self.assertEqual(my_bot.mouth.get().text, 'testy version 17.4.1')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
