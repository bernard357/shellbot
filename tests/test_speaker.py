#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, SparkSpace, Speaker


class SpeakerTests(unittest.TestCase):

    def test_static(self):

        logging.info('*** Static test ***')

        context = Context()
        mouth = Queue()
        space = SparkSpace(context=context)
        speaker = Speaker(mouth=mouth, space=space)

        speaker_process = Process(target=speaker.work, args=(context,))
        speaker_process.daemon = True
        speaker_process.start()

        speaker_process.join(1.0)
        if speaker_process.is_alive():
            logging.info('Stopping speaker')
            context.set('general.switch', 'off')
            speaker_process.join()

        self.assertFalse(speaker_process.is_alive())
        self.assertEqual(context.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        mouth = Queue()
        mouth.put('hello')
        mouth.put('world')
        mouth.put(Exception('EOQ'))

        context = Context()
        context.set('spark.CISCO_SPARK_PLUMBERY_BOT', 'garbage')
        context.set('spark.room_id', 'fake')

        space = SparkSpace(context=context)
        space.room_id = '123'
        speaker = Speaker(mouth=mouth, space=space)

        with mock.patch.object(space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.work(context)
            mocked.assert_any_call('hello')
            mocked.assert_called_with('world')

            with self.assertRaises(Exception):
                mouth.get_nowait()

    def test_process(self):

        logging.info('*** Processing test ***')

        context = Context()
        context.set('spark.CISCO_SPARK_PLUMBERY_BOT', 'garbage')
        context.set('spark.room_id', 'fake')

        space = SparkSpace(context=context)
        speaker = Speaker(mouth=Queue(), space=space)

        with mock.patch.object(space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.process('hello world', 1)
            mocked.assert_called_with('hello world')

            class WithMarkdown(object):
                message = ''
                markdown = 'me **too**'
                file = None

            item = WithMarkdown()
            speaker.process(item, 2)
            mocked.assert_called_with('',
                                      markdown='me **too**',
                                      file_path=None)

            class WithFile(object):
                message = '*with*attachment'
                markdown = None
                file = 'http://a.server/with/file'

            item = WithFile()
            speaker.process(item, 3)
            mocked.assert_called_with('*with*attachment',
                                      markdown=None,
                                      file_path='http://a.server/with/file')

            class WithAll(object):
                message = 'hello world'
                markdown = 'hello **world**'
                file = 'http://a.server/with/file'

            item = WithAll()
            speaker.process(item, 4)
            mocked.assert_called_with('hello world',
                                      markdown='hello **world**',
                                      file_path='http://a.server/with/file')

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
