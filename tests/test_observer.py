#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
from threading import Timer
import time

from shellbot import Context, Engine
from shellbot.events import Message
from shellbot.observer import Observer

class FakeMessage(object):
    channel_id = '*id1'
    text = "hello world"

my_message = FakeMessage()

class FakeUpdater(object):

    def __init__(self, id):
        self.id = id
        self.count = 0
        self.text = None

    def put(self, item):
        self.count += 1
        self.text = item.text
        logging.debug(u"- update: {}".format(item.text))

class FakeFactory(object):

    def get_updater(self, id):
        return FakeUpdater(id)

my_01_message_from_bot_in_group = Message({
    "channel_id": "*id1",
    "content": "<p>Hello there!</p>",
    "stamp": "2017-07-30T20:34:35.593Z",
    "files": ["http://hydra-a5.wbx2.com/MWU3LTg5MzgtZjU1MWY1ZTU1ZmE5LzA"],
    "from_id": "*shelly*id",
    "from_label": "shelly@sparkbot.io",
    "hook": "shellbot-audit",
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NBR0UvgtZjU1MWY1ZTU1ZmE5",
    "is_direct": False,
    "markdown": "Hello there!",
    "mentioned_ids": [],
    "personEmail": "shelly@sparkbot.io",
    "personId": "*shelly*id",
    "roomId": "*id1",
    "roomType": "group",
    "text": "Type '@shelly help' for more information",
    "type": "message",
})

my_03_message_from_person_in_group = Message({
    "channel_id": "*id1",
    "content": "<p>shelly hello</p>",
    "stamp": "2017-07-30T20:41:30.822Z",
    "from_id": "*foo*id",
    "from_label": "foo.bar@acme.com",
    "hook": "shellbot-audit",
    "html": "<p>shelly hello</p>",
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NU2Ny0xMWU3LTliMTctOTc4N2UzMWUzZWQ4",
    "is_direct": False,
    "mentionedPeople": ["*shelly*id"],
    "mentioned_ids": ["*shelly*id"],
    "personEmail": "foo.bar@acme.com",
    "personId": "*foo*id",
    "roomId": "*id1",
    "roomType": "group",
    "text": "shelly hello",
    "type": "message"
})

my_04_response_from_bot_in_group = Message({
    "channel_id": "*id1",
    "content": "Hello, World!",
    "stamp": "2017-07-30T20:41:33.104Z",
    "from_id": "*shelly*id",
    "from_label": "shelly@sparkbot.io",
    "hook": "shellbot-audit",
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NBR2Ny0xMWU3LWI4NWEtNDU3YmY3NDg5MmJh",
    "is_direct": False,
    "mentioned_ids": [],
    "personEmail": "shelly@sparkbot.io",
    "personId": "*shelly*id",
    "roomId": "*id1",
    "roomType": "group",
    "text": "Hello, World!",
    "type": "message"
})

my_05_message_out_of_scope_for_audit = Message({
    "channel_id": "*id2",
    "content": "sent in a channel where bot is not",
    "stamp": "2017-07-30T20:47:18.865Z",
    "from_id": "*foo*id",
    "from_label": "foo.bar@acme.com",
    "hook": "shellbot-audit",
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NBtNzU2OC0xMWU3LTlhOTctN2QxODMzMTU5MzJl",
    "is_direct": False,
    "mentioned_ids": [],
    "personEmail": "foo.bar@acme.com",
    "personId": "*foo*id",
    "roomId": "*id2",
    "roomType": "group",
    "text": "sent in a channel where bot is not",
    "type": "message"
})


class ObserverTests(unittest.TestCase):

    def setUp(self):
        self.fan = Queue()
        self.engine = Engine(updater_factory=FakeFactory(), fan=self.fan)
        self.engine.set('bots.ids', ['*id1'])

    def tearDown(self):
        del self.engine
        del self.fan
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        observer = Observer(engine=self.engine)

        observer.start()

        observer.join(0.1)
        if observer.is_alive():
            logging.info('Stopping observer')
            self.engine.set('general.switch', 'off')
            observer.join()

        self.assertFalse(observer.is_alive())
        self.assertEqual(self.engine.get('observer.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        self.engine.fan.put(my_message)
        self.engine.fan.put(None)

        observer = Observer(engine=self.engine)

        observer.run()

        with self.assertRaises(Exception):
            engine.fan.get_nowait()

    def test_start(self):

        logging.info("*** start")

        self.engine.fan.put(my_message)

        self.engine.set('general.switch', 'on')
        self.engine.set('observer.counter', 0) # do not wait for run()

        observer = Observer(engine=self.engine)
        observer.start()
        while True:
            counter = self.engine.get('observer.counter', 0)
            if counter > 0:
                logging.info("- observer.counter > 0")
                break
        self.engine.set('general.switch', 'off')
        observer.join()

        self.assertTrue(self.engine.get('observer.counter') > 0)

    def test_run(self):

        logging.info("*** run")

        self.engine.observer.process = mock.Mock(side_effect=Exception('TEST'))
        self.engine.fan.put(my_message)
        self.engine.fan.put(None)
        self.engine.observer.run()
        self.assertEqual(self.engine.get('observer.counter'), 0)

        self.engine.observer = Observer(engine=self.engine)
        self.engine.observer.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        self.engine.fan.put(my_message)
        self.engine.observer.run()
        self.assertEqual(self.engine.get('observer.counter'), 0)

    def test_run_wait(self):

        logging.info("*** run/wait while empty")

        self.engine.observer.NOT_READY_DELAY = 0.01
        self.engine.set('general.switch', 'on')
        self.engine.observer.start()

        t = Timer(0.1, self.engine.fan.put, [my_message])
        t.start()

        time.sleep(0.2)
        self.engine.set('general.switch', 'off')
        self.engine.observer.join()

    def test_process(self):

        logging.info('*** process ***')

        self.engine.set('audit.switch.*id1', 'on')

        observer = Observer(engine=self.engine)

        observer.process(my_message)

        updater = observer.updaters['*id1']

        self.assertEqual(updater.count, 2)  # because of self-generated msg
        self.assertEqual(updater.text, 'hello world')

        self.engine.set('audit.switch.*id1', 'off')

        observer.process(my_message)

        self.assertEqual(updater.count, 3)  # because of self-generated msg
        self.assertEqual(updater.text, '========== AUDIT OFF ==========')

        observer.process(my_01_message_from_bot_in_group)
        observer.process(my_03_message_from_person_in_group)
        observer.process(my_04_response_from_bot_in_group)
        observer.process(my_05_message_out_of_scope_for_audit)

        self.assertEqual(updater.count, 3)
        self.assertEqual(updater.text, '========== AUDIT OFF ==========')

        self.engine.set('audit.switch.*id1', 'on')

        observer.process(my_01_message_from_bot_in_group)
        self.assertEqual(updater.count, 5)  # because of self-generated msg
        self.assertEqual(updater.text, "Type '@shelly help' for more information")

        observer.process(my_03_message_from_person_in_group)
        self.assertEqual(updater.count, 6)
        self.assertEqual(updater.text, 'shelly hello')

        observer.process(my_04_response_from_bot_in_group)
        self.assertEqual(updater.count, 7)
        self.assertEqual(updater.text, 'Hello, World!')

        observer.process(my_05_message_out_of_scope_for_audit)
        self.assertEqual(updater.count, 7)  # not considered by observer


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
