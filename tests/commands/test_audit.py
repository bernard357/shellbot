#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.commands import Audit
from shellbot.events import Message


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
        c.off_duration = None

        my_bot.context.set('audit.switch', None)
        c.execute(u'')
        self.assertEqual(my_bot.mouth.get().text, c.disabled_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c._armed = True
        c.execute(u'')
        self.assertEqual(my_bot.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'on')
        self.assertEqual(my_bot.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'on')
        self.assertEqual(my_bot.mouth.get().text, c.already_on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'off')
        self.assertEqual(my_bot.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'off')
        self.assertEqual(my_bot.mouth.get().text, c.already_off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'')
        self.assertEqual(my_bot.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(u'*weird')
        self.assertEqual(my_bot.mouth.get().text, 'usage: audit [on|off]')
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

    def test_on_init(self):

        logging.info('***** on_init')

        c = Audit(my_bot)
        c.bot = mock.Mock()
        c.on_init()
        self.assertTrue(c.bot.register.called)

    def test_on_start(self):

        logging.info('***** on_start')

        c = Audit(my_bot)
        c.bot = mock.Mock()
        c.on_start()
        self.assertTrue(c.bot.say.called)

    def test_on_off(self):

        logging.info('***** on_off')

        class MyAudit(Audit):
            def watchdog(self):
                self.expected = True

        c = MyAudit(my_bot)
        c.off_duration = 0.001
        c.bot = mock.Mock()
        c.on_off()
        time.sleep(0.003)
        self.assertTrue(c.expected)

    def test_watchdog(self):

        logging.info('***** watchdog')

        c = Audit(my_bot)
        c.audit_on = mock.Mock()
        my_bot.context.set('audit.switch', 'off')
        c.watchdog()
        self.assertTrue(c.audit_on.called)

    def test_filter_on(self):

        logging.info('***** filter on')

        c = Audit(my_bot)

        class MyUpdater(object):
            queue = Queue()
            def put(self, event):
                self.queue.put(str(event))

        my_bot.context.set('audit.switch', 'on')

        c.updater = None

        item = Message({'text': 'hello world', 'person_label': 'a@me.com'})
        print(str(item))
        self.assertEqual(c.filter(item), item)

        c.updater = MyUpdater()
        self.assertEqual(c.filter(item), item)
        self.assertEqual(Message(c.updater.queue.get()), item)
        with self.assertRaises(Exception):
            c.updater.get_nowait()

    def test_filter_off(self):

        logging.info('***** filter off')

        c = Audit(my_bot)

        class MyUpdater(object):
            queue = Queue()
            def put(self, event):
                self.queue.put(str(event))

        my_bot.context.set('audit.switch', 'off')

        c.updater = None

        item = Message({'text': 'hello world', 'person_label': 'a@me.com'})
        self.assertEqual(c.filter(item), item)

        c.updater = MyUpdater()
        self.assertEqual(c.filter(item), item)
        with self.assertRaises(Exception):
            c.updater.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
