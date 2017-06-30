#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
from multiprocessing import Queue
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.routes.wrapper import Wrapper


class WrapperTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_wrapper(self):

        r = Wrapper(Context())

        with self.assertRaises(AttributeError):
            r.get()

        with self.assertRaises(AttributeError):
            r.post()

        with self.assertRaises(AttributeError):
            r.put()

        with self.assertRaises(AttributeError):
            r.delete()

        def hook():
            return 'hello'

        def hook_patched():
            return 'world'

        r = Wrapper(callable=hook,
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

        r = Wrapper(context=context,
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
