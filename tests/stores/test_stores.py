#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.stores import StoreFactory, MemoryStore, SqliteStore

my_context = Context()


class StoreFactoryTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()

    def test_build_memory(self):

        store = StoreFactory.build(context=my_context)
        self.assertTrue(isinstance(store, MemoryStore))

    def test_build_sqlite(self):

        my_context.apply(settings={  # from settings to member attributes
                           'sqlite': {
                               'db': 'my_store.db',
                           }
                       })

        store = StoreFactory.build(context=my_context)
        self.assertTrue(isinstance(store, SqliteStore))
        self.assertEqual(my_context.get('sqlite.db'), 'my_store.db')

    def test_sense(self):

        my_context.apply(settings={  # default is 'memory'
            'oracle': {
                'db': 'my_store.db',
            }
        })

        self.assertEqual(StoreFactory.sense(my_context), 'memory')

        my_context.clear()
        my_context.apply(settings={  # sense='sqlite'
            'sqlite': {
                'db': 'my_store.db',
            }
        })

        self.assertEqual(StoreFactory.sense(my_context), 'sqlite')

    def test_get_memory(self):

        store = StoreFactory.get(type='memory')
        self.assertTrue(isinstance(store, MemoryStore))

        store = StoreFactory.get(type='memory', context=my_context, weird='w')
        self.assertEqual(store.context, my_context)
        with self.assertRaises(AttributeError):
            self.assertEqual(store.weird, 'w')

    def test_get_sqlite(self):

        store = StoreFactory.get(type='sqlite', context=my_context)
        self.assertTrue(isinstance(store, SqliteStore))
        self.assertEqual(store.context, my_context)

    def test_get_unknown(self):

        with self.assertRaises(ValueError):
            store = StoreFactory.get(type='*unknown', ex_token='b', ex_ears='c')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
