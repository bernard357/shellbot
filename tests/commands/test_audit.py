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

class AuditTests(unittest.TestCase):

    def setUp(self):
        my_bot.shell = Shell(bot=my_bot)

    def test_audit(self):

        logging.info('***** audit')

        from shellbot.commands import Audit

        c = Audit(my_bot)

        self.assertEqual(c.keyword, u'audit')
        self.assertEqual(c.information_message,
                         u'Check and change audit status')
        self.assertEqual(c.usage_message, u'audit [on|off]')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        my_bot.context.set('audit.switch', None)
        c.execute(u'')
        self.assertEqual(my_bot.mouth.get(), c.disabled_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c._armed = True
        c.execute(u'')
        self.assertEqual(my_bot.mouth.get(), c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'on')
        self.assertEqual(my_bot.mouth.get(), c.on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get(), c.on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'on')
        self.assertEqual(my_bot.mouth.get(), c.already_on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get(), c.on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'off')
        self.assertEqual(my_bot.mouth.get(), c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get(), c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'off')
        self.assertEqual(my_bot.mouth.get(), c.already_off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get(), c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
