#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
import time
import yaml

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Audit
from shellbot.events import Message

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class MyChannel(object):
    is_group = True

class Bot(object):
    id = '*id'
    channel = MyChannel()

    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class AuditTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Audit(my_engine)

        self.assertEqual(c.keyword, u'audit')
        self.assertEqual(c.information_message,
                         u'Check and change audit status')
        self.assertEqual(c.usage_message, u'audit [on|off]')
        self.assertFalse(c.is_hidden)
        self.assertFalse(c.in_direct)
        self.assertTrue(c.in_group)

    def test_execute(self):

        logging.info('***** execute')

        c = Audit(my_engine)
        c.off_duration = None

        my_engine.set('audit.switch', None)
        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.disabled_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        my_engine.set('audit.has_been_armed', True)
        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'on')
        self.assertEqual(my_engine.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'on')
        self.assertEqual(my_engine.mouth.get().text, c.already_on_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'off')
        self.assertEqual(my_engine.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'off')
        self.assertEqual(my_engine.mouth.get().text, c.already_off_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.off_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, u'*weird')
        self.assertEqual(my_engine.mouth.get().text, 'usage: audit [on|off]')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_has_been_enabled(self):

        logging.info('***** has_been_enabled')

        my_engine.set('audit.has_been_armed', False)
        c = Audit(my_engine)
        self.assertFalse(c.has_been_enabled)

        my_engine.set('audit.has_been_armed', True)
        self.assertTrue(c.has_been_enabled)

    def test_on_init(self):

        logging.info('***** on_init')

        c = Audit(my_engine)
        c.engine = mock.Mock()
        c.on_init()
        self.assertTrue(c.engine.register.called)

    def test_on_bond(self):

        logging.info('***** on_bond')

        c = Audit(my_engine)
        c.on_bond(my_bot)
        self.assertEqual(my_engine.get('audit.switch.*id'), 'on')

    def test_on_off(self):

        logging.info('***** on_off')

        class MyAudit(Audit):
            def on_init(self):
                self.expected = False
            def watchdog(self, bot, **kwargs):
                self.expected = True

        c = MyAudit(my_engine)
        c.off_duration = 0.001
        c.engine = mock.Mock()
        c.on_off(my_bot)
        while True:
            time.sleep(0.001)
            if c.expected:
                break

        self.assertEqual(my_engine.mouth.get().text, c.on_message)
        self.assertEqual(
            my_engine.mouth.get().text,
            "Please note that auditing will restart after 0.001 seconds")
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

    def test_watchdog(self):

        logging.info('***** watchdog')

        c = Audit(my_engine)
        my_engine.set('audit.switch.*id', 'off')
        c.watchdog(bot=my_bot)

        self.assertEqual(my_engine.get('audit.switch.*id'), 'on')

        self.assertEqual(my_engine.mouth.get().text, c.on_message)
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
