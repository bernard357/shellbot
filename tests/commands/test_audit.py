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
from shellbot.commands import Audit


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)

class AuditTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Audit(my_bot)

        self.assertEqual(c.keyword, u'audit')
        self.assertEqual(c.information_message,
                         u'Check and change audit status')
        self.assertEqual(c.usage_message, u'audit [on|off]')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Audit(my_bot)

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

        c.execute(u'*weird')
        self.assertEqual(my_bot.mouth.get(), 'usage: audit [on|off]')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_arm(self):

        logging.info('***** arm')

        c = Audit(my_bot)

        updater = mock.Mock()
        c.arm(updater=updater)
        self.assertEqual(c.updater, updater)

        self.assertEqual(my_bot.listener.filter, c.filter)

    def test_armed(self):

        logging.info('***** armed')

        c = Audit(my_bot)
        self.assertFalse(c.armed)

        c._armed = True
        self.assertTrue(c.armed)

        c = Audit(my_bot)

        c.space = mock.Mock()
        self.assertFalse(c.armed)

        c.updater = Queue()
        self.assertFalse(c.armed)

        c.arm(updater=Queue())
        self.assertTrue(c.armed)

    def test_filter(self):

        logging.info('***** filter')

        my_bot.context.set('audit.switch', 'on')

        c = Audit(my_bot)
        c.updater = None

        item = {'text': 'hello world', 'personEmail': 'a@me.com'}
        self.assertEqual(c.filter(item=item), item)

        c.updater = Queue()
        self.assertEqual(c.filter(item=item), item)
        self.assertEqual(c.updater.get(),
                         {'text': 'hello world', 'personEmail': 'a@me.com'})
        with self.assertRaises(Exception):
            c.updater.get_nowait()



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
