#!/usr/bin/env python

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.speaker import Speaker
from shellbot.space import SparkSpace


class SpeakerTests(unittest.TestCase):

    def test_static(self):

        print('*** Static test ***')

        context = Context()
        mouth = Queue()
        space = SparkSpace(context=context)
        speaker = Speaker(mouth=mouth, space=space)

        speaker_process = Process(target=speaker.work, args=(context,))
        speaker_process.daemon = True
        speaker_process.start()

        speaker_process.join(1.0)
        if speaker_process.is_alive():
            print('Stopping speaker')
            context.set('general.switch', 'off')
            speaker_process.join()

        self.assertFalse(speaker_process.is_alive())
        self.assertEqual(context.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        print('*** Dynamic test ***')

        mouth = Queue()
        mouth.put('hello')
        mouth.put(Exception('EOQ'))

        context = Context()
        context.set('spark.CISCO_SPARK_PLUMBERY_BOT', 'garbage')
        context.set('spark.room_id', 'fake')

        space = SparkSpace(context=context)
        speaker = Speaker(mouth=mouth, space=space)

        with mock.patch.object(space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.work(context)
            mocked.assert_called_with('hello')

            with self.assertRaises(Exception):
                mouth.get_nowait()

if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
