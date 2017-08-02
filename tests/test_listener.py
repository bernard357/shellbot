#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import json
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
from threading import Timer
import time
import yaml

from shellbot import Context, Engine, Listener, SpaceFactory, Vibes
from shellbot.events import Event, Message, Join, Leave


class MyEngine(Engine):
    injected_bot = None
    def get_bot(self, id):
        logging.debug("Injecting test bot")
        return self.injected_bot


class MyChannel(object):
    is_direct = False


class MyBot(object):
    channel = MyChannel()

    id = '234'
    fan = Queue()

    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file, self.id))

    def on_enter(self):
        pass


my_message = Message({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "stamp" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "attachment" : "media.png",
    "url" : "http://www.example.com/images/media.png",
})

my_private_message = Message({
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NB0xMWU3LTljODctNTljZjJjNDRhYmIy",
    "roomId": "Y2lzY29zcGFyazovL3VzL1JP0zY2VmLWJiNDctOTZlZjA1NmJhYzFl",
    "roomType": "direct",
    "text": "test",
    "stamp": "2017-07-22T16:49:22.008Z",
    "hook": "shellbot-messages",
    "personEmail": "foo.bar@again.org",
    "personId": "Y2lzY29zcGFyazovL3VzL1LTQ5YzQtYTIyYi1mYWYwZWQwMjkyMzU",
    "content": "test",
    "from_id": 'Y2lzY29zcGFyazovL3VzL1LTQ5YzQtYTIyYi1mYWYwZWQwMjkyMzU',
    "from_label": 'foo.bar@again.org',
    'is_direct': True,
    "mentioned_ids": [],
    "channel_id": 'Y2lzY29zcGFyazovL3VzL1JP0zY2VmLWJiNDctOTZlZjA1NmJhYzFl',
})

my_join = Join({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "stamp" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "actor_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})

my_leave = Leave({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "spce_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "stamp" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "actor_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})

my_enter = Join({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "stamp" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "actor_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})

my_exit = Leave({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "stamp" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "actor_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})

my_event = Event({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "stamp" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})

class ListenerTests(unittest.TestCase):

    def setUp(self):
        self.engine = MyEngine(ears=Queue(), mouth=Queue())
        self.engine.configure()
        self.engine.set('bot.id', "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg")
        self.bot = MyBot(engine=self.engine)
        self.engine.injected_bot = self.bot

    def tearDown(self):
        del self.bot
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_work(self):

        logging.info("*** run")

        self.engine.set('general.switch', 'on')

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0
        listener.process = mock.Mock(side_effect=Exception('TEST'))
        self.engine.ears.put(('dummy'))
        self.engine.ears.put(None)
        listener.run()
        self.assertEqual(self.engine.get('listener.counter'), 0)

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0
        listener.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        self.engine.ears.put(('dummy'))
        listener.run()
        self.assertEqual(self.engine.get('listener.counter'), 0)

    def test_run_wait(self):

        logging.info("*** run/wait while empty and not ready")

        self.engine.listener.DEFER_DURATION = 0.0
        self.engine.set('general.switch', 'on')
        self.engine.listener.start()

        t = Timer(0.1, self.engine.ears.put, [str(my_message)])
        t.start()

        time.sleep(0.2)
        self.engine.set('general.switch', 'off')
        self.engine.listener.join()

    def test_process(self):

        logging.info('*** process ***')

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0

        self.engine.set('listener.counter', 22)
        with self.assertRaises(AssertionError):
            listener.process('hello world')
        self.assertEqual(self.engine.get('listener.counter'), 23)

        listener.on_message = mock.Mock()
        listener.process(str(my_message))
        self.assertEqual(self.engine.get('listener.counter'), 24)
        self.assertTrue(listener.on_message.called)

        listener.on_message = mock.Mock()
        listener.process(str(my_private_message))
        self.assertEqual(self.engine.get('listener.counter'), 25)
        self.assertTrue(listener.on_message.called)

        listener.on_join = mock.Mock()
        listener.process(str(my_join))
        self.assertEqual(self.engine.get('listener.counter'), 26)
        self.assertTrue(listener.on_join.called)

        listener.on_leave = mock.Mock()
        listener.process(str(my_leave))
        self.assertEqual(self.engine.get('listener.counter'), 27)
        self.assertTrue(listener.on_leave.called)

        listener.on_inbound = mock.Mock()
        listener.process(str(my_event))
        self.assertEqual(self.engine.get('listener.counter'), 28)
        self.assertTrue(listener.on_inbound.called)

    def test_process_filter(self):

        logging.info('*** process/filter ***')

        class Mocked(object):
            def filter(self, event):
                event.flag = True
                text = event.get('text')
                if text:
                    event.text = text.title()
                self.event = event
                return event

        mocked = Mocked()

        listener = Listener(engine=self.engine, filter=mocked.filter)
        listener.DEFER_DURATION = 0.0

        self.engine.set('listener.counter', 22)

        mocked.event = None
        listener.process(str(my_message))
        self.assertEqual(self.engine.get('listener.counter'), 23)
        self.assertEqual(mocked.event.text,
                         'The Pm For This Project Is Mike C. And The Engineering Manager Is Jane W.')
        self.assertTrue(mocked.event.flag)

        listener.process(str(my_private_message))
        self.assertEqual(self.engine.get('listener.counter'), 24)
        self.assertEqual(mocked.event.text, 'Test')
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_join))
        self.assertEqual(self.engine.get('listener.counter'), 25)
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_leave))
        self.assertEqual(self.engine.get('listener.counter'), 26)
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_event))
        self.assertEqual(self.engine.get('listener.counter'), 27)
        self.assertTrue(mocked.event.flag)

    def test_on_message(self):

        logging.info('*** on_message ***')

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0
        listener.on_message(my_message)
        listener.on_message(my_private_message)
        with self.assertRaises(AssertionError):
            listener.on_message(my_join)
        with self.assertRaises(AssertionError):
            listener.on_message(my_leave)
        with self.assertRaises(AssertionError):
            listener.on_message(my_event)

        with mock.patch.object(self.engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_message(my_message)
            self.assertTrue(mocked.called)

    def test_on_message_fan(self):

        logging.info('*** on_message/fan ***')

        self.engine.set('bot.id', '*not*for*me')

        class MyFan(object):
            def __init__(self):
                self.called = False
            def put(self, arguments):
                self.called = True

        self.bot.fan = MyFan()

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0

        listener.on_message(my_message)
        self.assertFalse(self.bot.fan.called)

        label = 'fan.' + my_message.channel_id
        logging.debug(u"- stamping '{}'".format(label))
        self.engine.set(label, time.time())
        listener.on_message(my_message)
        self.assertTrue(self.bot.fan.called)

    def test_on_join(self):

        logging.info('*** on_join ***')

        class Handler(object):

            def __init__(self):
                self.entered = False
                self.joined = False

            def on_enter(self, **kwargs):
                self.entered = True

            def on_join(self, **kwargs):
                self.joined = True

        handler = Handler()
        self.engine.register('enter', handler)
        self.engine.register('join', handler)

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0
        with self.assertRaises(AssertionError):
            listener.on_join(my_message)
        with self.assertRaises(AssertionError):
            listener.on_join(my_private_message)

        self.assertFalse(handler.entered)
        self.assertFalse(handler.joined)

        listener.on_join(my_enter)

        self.assertTrue(handler.entered)
        self.assertFalse(handler.joined)

        listener.on_join(my_join)

        self.assertTrue(handler.entered)
        self.assertTrue(handler.joined)

        with self.assertRaises(AssertionError):
            listener.on_join(my_leave)
        with self.assertRaises(AssertionError):
            listener.on_join(my_event)

        with mock.patch.object(self.engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_join(my_join)
            self.assertTrue(mocked.called)

    def test_on_leave(self):

        logging.info('*** on_leave ***')

        class Handler(object):

            def __init__(self):
                self.out = False
                self.left = False

            def on_exit(self, **kwargs):
                self.out = True

            def on_leave(self, **kwargs):
                self.left = True

        handler = Handler()
        self.engine.register('exit', handler)
        self.engine.register('leave', handler)

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0
        with self.assertRaises(AssertionError):
            listener.on_leave(my_message)
        with self.assertRaises(AssertionError):
            listener.on_leave(my_private_message)
        with self.assertRaises(AssertionError):
            listener.on_leave(my_join)

        self.assertFalse(handler.out)
        self.assertFalse(handler.left)

        listener.on_leave(my_exit)

        self.assertTrue(handler.out)
        self.assertFalse(handler.left)

        listener.on_leave(my_leave)

        self.assertTrue(handler.out)
        self.assertTrue(handler.left)

        with self.assertRaises(AssertionError):
            listener.on_leave(my_event)

        with mock.patch.object(self.engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_leave(my_leave)
            self.assertTrue(mocked.called)

    def test_on_inbound(self):

        logging.info('*** on_inbound ***')

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_message)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_private_message)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_join)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_leave)
        listener.on_inbound(my_event)

        with mock.patch.object(self.engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_inbound(my_event)
            self.assertTrue(mocked.called)

    def test_static(self):

        logging.info('*** Static test ***')

        listener = Listener(engine=self.engine)
        listener.DEFER_DURATION = 0.0

        listener.start()

        listener.join(0.1)
        if listener.is_alive():
            logging.info('Stopping listener')
            self.engine.set('general.switch', 'off')
            listener.join()

        self.assertFalse(listener.is_alive())
        self.assertEqual(self.engine.get('listener.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        items = [

            {
              "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "PROJECT UPDATE - A new project plan has been published on Box: http://box.com/s/lf5vj. The PM for this project is Mike C. and the Engineering Manager is Jane W.",
              "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
              "files" : [ "http://www.example.com/images/media.png" ],
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "stamp" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
            },

            {
              "id" : "2_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "/shelly version",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "stamp" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
            },

            {
              "id" : "2_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "stamp" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
            },

            {
              "id" : "3_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "@shelly help",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "stamp" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
            },

            {
              "id" : "3_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "!shelly help help",
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "stamp" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
            },

            {
              "id" : "4_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
              "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
              "roomType" : "group",
              "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
              "toPersonEmail" : "julie@example.com",
              "text" : "PROJECT UPDATE - A new project plan has been published on Box: http://box.com/s/lf5vj. The PM for this project is Mike C. and the Engineering Manager is Jane W.",
              "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
              "files" : [ "http://www.example.com/images/media.png" ],
              "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "personEmail" : "matt@example.com",
              "stamp" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM" ],
            },

            {
                "id": "Y2lzY29zcGFyazovL3VzL01FU1NB0xMWU3LTljODctNTljZjJjNDRhYmIy",
                "roomId": "Y2lzY29zcGFyazovL3VzL1JP0zY2VmLWJiNDctOTZlZjA1NmJhYzFl",
                "roomType": "direct",
                "text": "test",
                "stamp": "2017-07-22T16:49:22.008Z",
                "hook": "shellbot-messages",
                "personEmail": "foo.bar@again.org",
                "personId": "Y2lzY29zcGFyazovL3VzL1LTQ5YzQtYTIyYi1mYWYwZWQwMjkyMzU",
                "content": "test",
                "from_id": 'Y2lzY29zcGFyazovL3VzL1LTQ5YzQtYTIyYi1mYWYwZWQwMjkyMzU',
                "from_label": 'foo.bar@again.org',
                'is_direct': True,
                "mentioned_ids": [],
                "channel_id": 'Y2lzY29zcGFyazovL3VzL1JP0zY2VmLWJiNDctOTZlZjA1NmJhYzFl',
            },
        ]

        for item in items:
            self.engine.ears.put(str(Message(item)))

        self.engine.ears.put(None)

        tee = Queue()

        def filter(item):
            tee.put(str(item))
            return item

        listener = Listener(engine=self.engine, filter=filter)
        listener.DEFER_DURATION = 0.0

        listener.run()

        self.assertEqual(self.engine.get('listener.counter'), 7)
        with self.assertRaises(Exception):
            self.engine.ears.get_nowait()
        self.assertEqual(
            self.engine.mouth.get_nowait().text,
            'Shelly version *unknown*')
        self.assertEqual(
            self.engine.mouth.get_nowait().text,
            u'Available commands:\n'
            + u'help - Show commands and usage')
        self.assertEqual(
            self.engine.mouth.get_nowait().text,
            u'Available commands:\n'
            + u'help - Show commands and usage')
        self.assertEqual(
            self.engine.mouth.get_nowait().text,
            u'help - Show commands and usage\nusage: help <command>')
        self.assertEqual(
            self.engine.mouth.get_nowait().text,
            u"Sorry, I do not know how to handle 'test'")
        with self.assertRaises(Exception):
            print(self.engine.mouth.get_nowait())

        self.maxDiff = None
        for item in items:
            item.update({'type': 'message'})
            self.assertEqual(yaml.safe_load(tee.get()), item)
        with self.assertRaises(Exception):
            print(tee.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
