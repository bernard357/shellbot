#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
from multiprocessing import Queue
import sys

from shellbot import Context
from shellbot.routes.notifier import Notifier


class NotifyTests(unittest.TestCase):

    def test_notify(self):

        r = Notifier(Context())
        self.assertEqual(r.route, '/notify')
        self.assertTrue(r.queue is not None)
        self.assertEqual(r.notification, None)
        with self.assertRaises(Exception):
            r.get()

        queue = Queue()
        r = Notifier(Context(), queue=queue, route='/test')
        self.assertEqual(r.queue, queue)
        self.assertEqual(r.notification, None)
        self.assertEqual(r.get(), 'OK')
        self.assertEqual(queue.get(), '/test')

        queue = Queue()
        r = Notifier(Context(), queue=queue, notification='signal')
        self.assertEqual(r.queue, queue)
        self.assertEqual(r.notification, 'signal')

        self.assertEqual(r.get(), 'OK')
        self.assertEqual(queue.get(), 'signal')

        self.assertEqual(r.post(), 'OK')
        self.assertEqual(queue.get(), 'signal')

        self.assertEqual(r.put(), 'OK')
        self.assertEqual(queue.get(), 'signal')

        self.assertEqual(r.delete(), 'OK')
        self.assertEqual(queue.get(), 'signal')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
