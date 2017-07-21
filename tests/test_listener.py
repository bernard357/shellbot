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
from shellbot.events import Event, Message, Attachment, Join, Leave


class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("Injecting test bot")
        return my_bot


my_engine = MyEngine(ears=Queue(), mouth=Queue())
my_engine.shell.load_default_commands()


class MyBot(object):
    channel_id = '234'
    fan = Queue()

    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file, self.channel_id))


my_bot = MyBot(engine=my_engine)


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
    "created" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})

my_attachment = Attachment({
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "channel_id" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "url" : "http://www.example.com/images/media.png",
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "created" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
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
    "created" : "2015-10-18T14:26:16+00:00",
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
    "created" : "2015-10-18T14:26:16+00:00",
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
    "created" : "2015-10-18T14:26:16+00:00",
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
    "created" : "2015-10-18T14:26:16+00:00",
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
    "created" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
})



class ListenerTests(unittest.TestCase):

    def setUp(self):
        my_engine.set('bot.id', "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg")

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_work(self):

        logging.info("*** run")

        my_engine.set('general.switch', 'on')

        listener = Listener(engine=my_engine)
        listener.process = mock.Mock(side_effect=Exception('TEST'))
        my_engine.ears.put(('dummy'))
        my_engine.ears.put(None)
        listener.run()
        self.assertEqual(my_engine.get('listener.counter'), 0)

        listener = Listener(engine=my_engine)
        listener.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        my_engine.ears.put(('dummy'))
        listener.run()
        self.assertEqual(my_engine.get('listener.counter'), 0)

    def test_run_wait(self):

        logging.info("*** run/wait while empty and not ready")

        my_engine.set('general.switch', 'on')
        listener_process = my_engine.listener.start()

        t = Timer(0.1, my_engine.ears.put, [str(my_message)])
        t.start()

        time.sleep(0.2)
        my_engine.set('general.switch', 'off')
        listener_process.join()

    def test_process(self):

        logging.info('*** process ***')

        listener = Listener(engine=my_engine)

        my_engine.set('listener.counter', 22)
        with self.assertRaises(AssertionError):
            listener.process('hello world')
        self.assertEqual(my_engine.get('listener.counter'), 23)

        listener.on_message = mock.Mock()
        listener.process(str(my_message))
        self.assertEqual(my_engine.get('listener.counter'), 24)
        self.assertTrue(listener.on_message.called)

        listener.on_attachment = mock.Mock()
        listener.process(str(my_attachment))
        self.assertEqual(my_engine.get('listener.counter'), 25)
        self.assertTrue(listener.on_attachment.called)

        listener.on_join = mock.Mock()
        listener.process(str(my_join))
        self.assertEqual(my_engine.get('listener.counter'), 26)
        self.assertTrue(listener.on_join.called)

        listener.on_leave = mock.Mock()
        listener.process(str(my_leave))
        self.assertEqual(my_engine.get('listener.counter'), 27)
        self.assertTrue(listener.on_leave.called)

        listener.on_inbound = mock.Mock()
        listener.process(str(my_event))
        self.assertEqual(my_engine.get('listener.counter'), 28)
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

        listener = Listener(engine=my_engine, filter=mocked.filter)

        my_engine.set('listener.counter', 22)

        mocked.event = None
        listener.process(str(my_message))
        self.assertEqual(my_engine.get('listener.counter'), 23)
        self.assertEqual(mocked.event.text,
                         'The Pm For This Project Is Mike C. And The Engineering Manager Is Jane W.')
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_attachment))
        self.assertEqual(my_engine.get('listener.counter'), 24)
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_join))
        self.assertEqual(my_engine.get('listener.counter'), 25)
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_leave))
        self.assertEqual(my_engine.get('listener.counter'), 26)
        self.assertTrue(mocked.event.flag)

        mocked.event = None
        listener.process(str(my_event))
        self.assertEqual(my_engine.get('listener.counter'), 27)
        self.assertTrue(mocked.event.flag)

    def test_on_message(self):

        logging.info('*** on_message ***')

        listener = Listener(engine=my_engine)
        listener.on_message(my_message)
        with self.assertRaises(AssertionError):
            listener.on_message(my_attachment)
        with self.assertRaises(AssertionError):
            listener.on_message(my_join)
        with self.assertRaises(AssertionError):
            listener.on_message(my_leave)
        with self.assertRaises(AssertionError):
            listener.on_message(my_event)

        with mock.patch.object(my_engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_message(my_message)
            self.assertTrue(mocked.called)

    def test_on_message_fan(self):

        logging.info('*** on_message/fan ***')

        my_engine.set('bot.id', '*not*for*me')

        class MyFan(object):
            def __init__(self):
                self.called = False
            def put(self, arguments):
                self.called = True

        my_bot.fan = MyFan()

        listener = Listener(engine=my_engine)

        listener.on_message(my_message)
        self.assertFalse(my_bot.fan.called)

        label = 'fan.' + my_message.channel_id
        logging.debug(u"- stamping '{}'".format(label))
        my_engine.set(label, time.time())
        listener.on_message(my_message)
        self.assertTrue(my_bot.fan.called)

    def test_on_attachment(self):

        logging.info('*** on_attachment ***')

        listener = Listener(engine=my_engine)
        with self.assertRaises(AssertionError):
            listener.on_attachment(my_message)
        listener.on_attachment(my_attachment)
        with self.assertRaises(AssertionError):
            listener.on_attachment(my_join)
        with self.assertRaises(AssertionError):
            listener.on_attachment(my_leave)
        with self.assertRaises(AssertionError):
            listener.on_attachment(my_event)

        with mock.patch.object(my_engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_attachment(my_attachment)
            self.assertTrue(mocked.called)

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
        my_engine.subscribe('enter', handler)
        my_engine.subscribe('join', handler)

        listener = Listener(engine=my_engine)
        with self.assertRaises(AssertionError):
            listener.on_join(my_message)
        with self.assertRaises(AssertionError):
            listener.on_join(my_attachment)

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

        with mock.patch.object(my_engine,
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
        my_engine.subscribe('exit', handler)
        my_engine.subscribe('leave', handler)

        listener = Listener(engine=my_engine)
        with self.assertRaises(AssertionError):
            listener.on_leave(my_message)
        with self.assertRaises(AssertionError):
            listener.on_leave(my_attachment)
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

        with mock.patch.object(my_engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_leave(my_leave)
            self.assertTrue(mocked.called)

    def test_on_inbound(self):

        logging.info('*** on_inbound ***')

        listener = Listener(engine=my_engine)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_message)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_attachment)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_join)
        with self.assertRaises(AssertionError):
            listener.on_inbound(my_leave)
        listener.on_inbound(my_event)

        with mock.patch.object(my_engine,
                               'dispatch',
                               return_value=None) as mocked:
            listener.on_inbound(my_event)
            self.assertTrue(mocked.called)

    def test_static(self):

        logging.info('*** Static test ***')

        listener = Listener(engine=my_engine)

        listener_process = listener.start()

        listener_process.join(0.1)
        if listener_process.is_alive():
            logging.info('Stopping listener')
            my_engine.set('general.switch', 'off')
            listener_process.join()

        self.assertFalse(listener_process.is_alive())
        self.assertEqual(my_engine.get('listener.counter', 0), 0)

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
              "created" : "2015-10-18T14:26:16+00:00",
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
              "created" : "2015-10-18T14:26:16+00:00",
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
              "created" : "2015-10-18T14:26:16+00:00",
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
              "created" : "2015-10-18T14:26:16+00:00",
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
              "created" : "2015-10-18T14:26:16+00:00",
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
              "created" : "2015-10-18T14:26:16+00:00",
              "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
              "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
              "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM" ],
            },

        ]

        for item in items:
            my_engine.ears.put(str(Message(item)))

        my_engine.ears.put(None)

        tee = Queue()

        def filter(item):
            tee.put(str(item))
            return item

        listener = Listener(engine=my_engine, filter=filter)

        listener.run()

        self.assertEqual(my_engine.get('listener.counter'), 6)
        with self.assertRaises(Exception):
            my_engine.ears.get_nowait()
        with self.assertRaises(Exception):
            my_engine.inbox.get_nowait()
        self.assertEqual(
            my_engine.mouth.get_nowait().text,
            'Shelly version *unknown*')
        self.assertEqual(
            my_engine.mouth.get_nowait().text,
            u'Available commands:\n'
            + u'help - Show commands and usage')
        self.assertEqual(
            my_engine.mouth.get_nowait().text,
            u'Available commands:\n'
            + u'help - Show commands and usage')
        self.assertEqual(
            my_engine.mouth.get_nowait().text,
            u'help - Show commands and usage\nusage: help <command>')
        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

        self.maxDiff = None
        for item in items:
            item.update({'type': 'message'})
            self.assertEqual(yaml.safe_load(tee.get()), item)
        with self.assertRaises(Exception):
            print(tee.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
