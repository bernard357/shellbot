#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

from shellbot import Context
from shellbot.stores import StoreFactory, MemoryStore, SqliteStore


class StoreFactoryTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()

    def tearDown(self):
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_build_memory(self):

        store = StoreFactory.build(context=self.context)
        self.assertTrue(isinstance(store, MemoryStore))

    def test_build_sqlite(self):

        self.context.apply(settings={  # from settings to member attributes
                           'sqlite': {
                               'db': 'self.store.db',
                           }
                       })

        store = StoreFactory.build(context=self.context)
        self.assertTrue(isinstance(store, SqliteStore))
        self.assertEqual(self.context.get('sqlite.db'), 'self.store.db')

    def test_sense(self):

        self.context.apply(settings={  # default is 'memory'
            'oracle': {
                'db': 'self.store.db',
            }
        })

        self.assertEqual(StoreFactory.sense(self.context), 'memory')

        self.context.clear()
        self.context.apply(settings={  # sense='sqlite'
            'sqlite': {
                'db': 'self.store.db',
            }
        })

        self.assertEqual(StoreFactory.sense(self.context), 'sqlite')

    def test_get_memory(self):

        store = StoreFactory.get(type='memory')
        self.assertTrue(isinstance(store, MemoryStore))

        store = StoreFactory.get(type='memory', context=self.context, weird='w')
        self.assertEqual(store.context, self.context)
        with self.assertRaises(AttributeError):
            self.assertEqual(store.weird, 'w')

    def test_get_sqlite(self):

        store = StoreFactory.get(type='sqlite', context=self.context)
        self.assertTrue(isinstance(store, SqliteStore))
        self.assertEqual(store.context, self.context)

    def test_get_unknown(self):

        with self.assertRaises(ValueError):
            store = StoreFactory.get(type='*unknown', ex_token='b', ex_ears='c')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
