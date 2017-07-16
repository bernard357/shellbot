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

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Audit
from shellbot.events import Message

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
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

    def test_execute(self):

        logging.info('***** execute')

        c = Audit(my_engine)
        c.off_duration = None

        my_engine.set('audit.switch', None)
        c.execute(my_bot, u'')
        self.assertEqual(my_engine.mouth.get().text, c.disabled_message)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c._armed = True
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

    def test_arm(self):

        logging.info('***** arm')

        c = Audit(my_engine)

        updater = mock.Mock()
        c.arm(updater=updater)
        self.assertEqual(c.updater, updater)

        self.assertEqual(my_engine.listener.filter, c.filter)

    def test_armed(self):

        logging.info('***** armed')

        c = Audit(my_engine)
        self.assertFalse(c.armed)

        c._armed = True
        self.assertTrue(c.armed)

        c = Audit(my_engine)

        c.space = mock.Mock()
        self.assertFalse(c.armed)

        c.updater = Queue()
        self.assertFalse(c.armed)

        c.arm(updater=Queue())
        self.assertTrue(c.armed)

    def test_on_init(self):

        logging.info('***** on_init')

        c = Audit(my_engine)
        c.engine = mock.Mock()
        c.on_init()
        self.assertTrue(c.engine.subscribe.called)

    def test_on_start(self):

        logging.info('***** on_start')

        c = Audit(my_engine)
        c.on_start()
        self.assertEqual(my_engine.get('audit.switch'), 'on')

    def test_on_off(self):

        logging.info('***** on_off')

        class MyAudit(Audit):
            def on_init(self):
                self.expected = False
            def watchdog(self):
                self.expected = True

        c = MyAudit(my_engine)
        c.off_duration = 0.001
        c.engine = mock.Mock()
        c.on_off(my_bot)
        while True:
            time.sleep(0.001)
            if c.expected:
                break

    def test_watchdog(self):

        logging.info('***** watchdog')

        c = Audit(my_engine)
        c.audit_on = mock.Mock()
        my_engine.set('audit.switch', 'off')
        c.watchdog()
        self.assertEqual(my_engine.get('audit.switch'), 'on')

    def test_filter_on(self):

        logging.info('***** filter on')

        c = Audit(my_engine)

        class MyUpdater(object):
            queue = Queue()
            def put(self, event):
                self.queue.put(str(event))

        my_engine.set('audit.switch', 'on')

        c.updater = None

        item = Message({'text': 'hello world', 'person_label': 'a@me.com'})
        self.assertEqual(c.filter(item), item)

        c.updater = MyUpdater()
        self.assertEqual(c.filter(item), item)
        self.assertEqual(Message(c.updater.queue.get()), item)
        with self.assertRaises(Exception):
            c.updater.get_nowait()

    def test_filter_off(self):

        logging.info('***** filter off')

        c = Audit(my_engine)

        class MyUpdater(object):
            queue = Queue()
            def put(self, event):
                self.queue.put(str(event))

        my_engine.set('audit.switch', 'off')

        c.updater = None

        item = Message({'text': 'hello world', 'person_label': 'a@me.com'})
        self.assertEqual(c.filter(item), item)

        c.updater = MyUpdater()
        self.assertEqual(c.filter(item), item)
        with self.assertRaises(Exception):
            c.updater.get_nowait()

    def test_say(self):

        logging.info('***** say')

        c = Audit(my_engine)

        class MyUpdater(object):
            queue = Queue()
            def put(self, event):
                self.queue.put(str(event))

        my_engine.set('audit.switch', 'on')

        c.updater = MyUpdater()
        c.say('hello world')
        item = c.updater.queue.get()
        self.assertEqual(yaml.safe_load(item),
                         {"from_id": "Shelly", "from_label": "Shelly", "text": "hello world", "type": "message"})
        with self.assertRaises(Exception):
            c.updater.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
