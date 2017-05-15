#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
from multiprocessing import Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Route


class CommandsTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

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

        self.assertEqual(r.post(), 'OK')
        self.assertEqual(queue.get(), 'signal')

        self.assertEqual(r.put(), 'OK')
        self.assertEqual(queue.get(), 'signal')

        self.assertEqual(r.delete(), 'OK')
        self.assertEqual(queue.get(), 'signal')

    def test_text(self):

        from shellbot.routes.text import Text

        r = Text(Context())
        self.assertEqual(r.route, '/')
        self.assertEqual(r.page, None)
        self.assertEqual(r.get(), 'OK')

        r = Text(Context(), route='/hello', page='Hello world')
        self.assertEqual(r.route, '/hello')
        self.assertEqual(r.page, 'Hello world')
        self.assertEqual(r.get(), 'Hello world')

    def test_wrapper(self):

        from shellbot.routes.wrap import Wrap

        r = Wrap(Context())

        with self.assertRaises(NotImplementedError):
            r.get()

        with self.assertRaises(NotImplementedError):
            r.post()

        with self.assertRaises(NotImplementedError):
            r.put()

        with self.assertRaises(NotImplementedError):
            r.delete()

        def hook():
            return 'hello'

        def hook_patched():
            return 'world'

        r = Wrap(callable=hook,
                    route='/wrapped')

        self.assertEqual(r.route, '/wrapped')
        self.assertTrue(r.callable is not None)
        self.assertEqual(r.get(), 'hello')
        self.assertEqual(r.post(), 'hello')
        self.assertEqual(r.put(), 'hello')
        self.assertEqual(r.delete(), 'hello')

        r.callable = hook_patched
        self.assertEqual(r.get(), 'world')
        self.assertEqual(r.post(), 'world')
        self.assertEqual(r.put(), 'world')
        self.assertEqual(r.delete(), 'world')

        context = Context()

        class Callable(object):
            def __init__(self, context):
                self.context = context

            def hook(self, **kwargs):
                self.context.set('signal', 'wrapped!')
                return 'OK'

        callable = Callable(context)

        r = Wrap(context=context,
                 callable=callable.hook,
                 route='/wrapped')

        self.assertEqual(r.route, '/wrapped')
        self.assertEqual(r.callable, callable.hook)
        self.assertEqual(context.get('signal'), None)
        self.assertEqual(r.get(), 'OK')
        self.assertEqual(r.post(), 'OK')
        self.assertEqual(r.put(), 'OK')
        self.assertEqual(r.delete(), 'OK')
        self.assertEqual(context.get('signal'), 'wrapped!')

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
