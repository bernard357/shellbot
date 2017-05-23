#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
import yaml

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.events import Message
from shellbot.updaters import QueueUpdater

my_bot = ShellBot()


class UpdaterTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        u = QueueUpdater()
        self.assertEqual(u.bot, None)

        u = QueueUpdater(bot=my_bot)
        self.assertEqual(u.bot, my_bot)

    def test_on_init(self):

        logging.info('***** on_init')

        u = QueueUpdater()
        self.assertTrue(u.queue not in (None, ''))

        u = QueueUpdater(queue=None)
        self.assertTrue(u.queue not in (None, ''))

        u = QueueUpdater(queue='')
        self.assertTrue(u.queue not in (None, ''))

        q = Queue()
        u = QueueUpdater(queue=q)
        self.assertEqual(u.queue, q)

    def test_put(self):

        logging.info('***** put')

        u = QueueUpdater()

        message_1 = Message({
            'person_label': 'alice@acme.com',
            'text': 'a first message',
        })
        u.put(message_1)

        message_2 = Message({
            'person_label': 'bob@acme.com',
            'text': 'a second message',
        })
        u.put(message_2)

        message_1.attributes.update({"type": "message"})
        self.assertEqual(yaml.safe_load(u.queue.get()), message_1.attributes)

        message_2.attributes.update({"type": "message"})
        self.assertEqual(yaml.safe_load(u.queue.get()), message_2.attributes)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
