#!/usr/bin/env python

import unittest
import logging
from mock import MagicMock
from multiprocessing import Process, Queue
import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.sender import Sender


class SenderTests(unittest.TestCase):

    def test_static(self):

        print('*** Static test ***')

        mouth = Queue()

        context = Context()
        sender = Sender(mouth)

        sender_process = Process(target=sender.work, args=(context,))
        sender_process.daemon = True
        sender_process.start()

        sender_process.join(1.0)
        if sender_process.is_alive():
            print('Stopping sender')
            context.set('general.switch', 'off')
            sender_process.join()

        self.assertFalse(sender_process.is_alive())
        self.assertEqual(context.get('sender.counter', 0), 0)

    def test_dynamic(self):

        print('*** Processing test ***')

        mouth = Queue()
        mouth.put('hello')
        mouth.put('world')
        mouth.put(Exception('EOQ'))

        context = Context()
        context.set('spark.CISCO_SPARK_PLUMBERY_BOT', 'garbage')
        context.set('spark.room_id', 'fake')

        sender = Sender(mouth)
#        sender.post_update = MagicMock()
        sender.work(context)

        with self.assertRaises(Exception):
            mouth.get_nowait()

if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
