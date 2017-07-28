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

from shellbot import Context, Engine, Speaker, SpaceFactory, Vibes

class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("injecting test bot")
        return my_bot


my_engine = MyEngine(mouth=Queue())


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class SpeakerTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        speaker = Speaker(engine=my_engine)

        speaker.start()

        speaker.join(0.1)
        if speaker.is_alive():
            logging.info('Stopping speaker')
            my_engine.set('general.switch', 'off')
            speaker.join()

        self.assertFalse(speaker.is_alive())
        self.assertEqual(my_engine.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        my_engine.space = SpaceFactory.get('local', engine=my_engine)

        items = ['hello', 'world']
        for item in items:
            my_engine.mouth.put(item)
        my_engine.mouth.put(None)

        speaker = Speaker(engine=my_engine)

        with mock.patch.object(my_engine.space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.run()
            mocked.assert_any_call(id='*default', text='hello')
            mocked.assert_called_with(id='*default', text='world')

            with self.assertRaises(Exception):
                engine.mouth.get_nowait()

    def test_start(self):

        logging.info("*** start")

        my_engine.space = SpaceFactory.get('local', engine=my_engine)
        my_engine.mouth.put('ping')

        my_engine.space.post_message = mock.Mock()
        my_engine.set('general.switch', 'on')
        my_engine.set('speaker.counter', 0) # do not wait for run()

        speaker = Speaker(engine=my_engine)
        speaker.start()
        while True:
            counter = my_engine.get('speaker.counter', 0)
            if counter > 0:
                logging.info("- speaker.counter > 0")
                break
        my_engine.set('general.switch', 'off')
        speaker.join()

        self.assertTrue(my_engine.get('speaker.counter') > 0)

    def test_run(self):

        logging.info("*** run")

        my_engine.space = SpaceFactory.get('local', engine=my_engine)

        my_engine.speaker.process = mock.Mock(side_effect=Exception('TEST'))
        my_engine.mouth.put(('dummy'))
        my_engine.mouth.put(None)
        my_engine.speaker.run()
        self.assertEqual(my_engine.get('speaker.counter'), 0)

        my_engine.speaker = Speaker(engine=my_engine)
        my_engine.speaker.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        my_engine.mouth.put(('dummy'))
        my_engine.speaker.run()
        self.assertEqual(my_engine.get('speaker.counter'), 0)

    def test_run_wait(self):

        logging.info("*** run/wait while empty")

        my_engine.space = SpaceFactory.get('local', engine=my_engine)

        my_engine.speaker.NOT_READY_DELAY = 0.01
        my_engine.set('general.switch', 'on')
        my_engine.speaker.start()

        t = Timer(0.1, my_engine.mouth.put, ['ping'])
        t.start()

        time.sleep(0.2)
        my_engine.set('general.switch', 'off')
        my_engine.speaker.join()

    def test_process(self):

        logging.info('*** process ***')

        speaker = Speaker(engine=my_engine)

        speaker.process('hello world')

        my_engine.space = SpaceFactory.get('local', engine=my_engine)

        speaker = Speaker(engine=my_engine)

        with mock.patch.object(my_engine.space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.process('hello world')
            mocked.assert_called_with(id='*default', text='hello world')

            item = Vibes(
                text='',
                content='me **too**',
                file=None,
                channel_id='123')
            speaker.process(item)
            mocked.assert_called_with(content='me **too**', file=None, id='123', person=None, text='')

            item = Vibes(
                text='',
                content='me **too**',
                file=None,
                person='a@b.com')
            speaker.process(item)
            mocked.assert_called_with(content='me **too**', file=None, id=None, person='a@b.com', text='')

            item = Vibes(
                text='*with*attachment',
                content=None,
                file='http://a.server/with/file',
                channel_id='456')
            speaker.process(item)
            mocked.assert_called_with(content=None, file='http://a.server/with/file', id='456', person=None, text='*with*attachment')

            item = Vibes(
                text='hello world',
                content='hello **world**',
                file='http://a.server/with/file',
                channel_id='789')
            speaker.process(item)
            mocked.assert_called_with(content='hello **world**', file='http://a.server/with/file', id='789', person=None, text='hello world')

            item = Vibes(
                text='hello world',
                content='hello **world**',
                file='http://a.server/with/file',
                channel_id='007')
            speaker.process(item)
            mocked.assert_called_with(content='hello **world**', file='http://a.server/with/file', id='007', person=None, text='hello world')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
