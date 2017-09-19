#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
from multiprocessing import Queue
import sys

from shellbot import Context, Route


class RouteTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_base(self):

        settings = {
            u'hello': u'world',
        }
        context = Context(settings)

        r = Route(context)
        self.assertEqual(r.context.get('hello'), u'world')
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


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
