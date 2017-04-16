#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorlog
import unittest
import logging
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Route


class CommandsTests(unittest.TestCase):

    def test_base(self):

        settings = {
            u'hello': u'world',
        }
        context = Context(settings)

        r = Route(context)
        self.assertEqual(r.context.get('general.hello'), u'world')
        self.assertEqual(r.route, None)

        with self.assertRaises(NotImplementedError):
            r.get()

        with self.assertRaises(NotImplementedError):
            r.post()

        with self.assertRaises(NotImplementedError):
            r.put()

        with self.assertRaises(NotImplementedError):
            r.delete()

    def test_from_base(self):

        w = ['world']
        q = Queue()
        r = Route(Context(), arg_1='hello', arg_2=w, arg_3=q, route='/ping')
        self.assertEqual(r.arg_1, 'hello')
        self.assertEqual(r.arg_2, w)
        self.assertEqual(r.arg_3, q)
        self.assertEqual(r.route, '/ping')

    def test_notify(self):

        from shellbot.routes.notify import Notify

        r = Notify(Context())
        self.assertEqual(r.route, '/notify')
        self.assertTrue(r.queue is not None)
        self.assertEqual(r.notification, None)
        with self.assertRaises(Exception):
            r.get()

        queue = Queue()
        r = Notify(Context(), queue=queue, route='/test')
        self.assertEqual(r.queue, queue)
        self.assertEqual(r.notification, None)
        self.assertEqual(r.get(), 'OK')
        self.assertEqual(queue.get(), '/test')

        queue = Queue()
        r = Notify(Context(), queue=queue, notification='signal')
        self.assertEqual(r.queue, queue)
        self.assertEqual(r.notification, 'signal')
        self.assertEqual(r.get(), 'OK')
        self.assertEqual(queue.get(), 'signal')

    def test_static(self):

        from shellbot.routes.static import Static

        r = Static(Context())
        self.assertEqual(r.route, '/')
        self.assertEqual(r.page, None)
        self.assertEqual(r.get(), 'OK')

        r = Static(Context(), route='/hello', page='Hello world')
        self.assertEqual(r.route, '/hello')
        self.assertEqual(r.page, 'Hello world')
        self.assertEqual(r.get(), 'Hello world')

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
