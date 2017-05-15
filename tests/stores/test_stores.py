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

from shellbot import Context, ShellBot
from shellbot.stores import StoreFactory, MemoryStore, SqliteStore

my_bot = ShellBot()


class StoreFactoryTests(unittest.TestCase):

    def test_build_memory(self):

        bot = ShellBot(space=mock.Mock())
        store = StoreFactory.build(bot=bot)
        self.assertTrue(isinstance(store, MemoryStore))

    def test_build_sqlite(self):

        bot = ShellBot(settings={  # from settings to member attributes
                           'sqlite': {
                               'db': 'my_store.db',
                           }
                       },
                       space=mock.Mock())

        store = StoreFactory.build(bot=bot)
        self.assertTrue(isinstance(store, SqliteStore))
        self.assertEqual(bot.context.get('sqlite.db'), 'my_store.db')

    def test_sense(self):

        context = Context(settings={  # default is 'memory'
            'oracle': {
                'db': 'my_store.db',
            }
        })

        self.assertEqual(StoreFactory.sense(context), 'memory')

        context = Context(settings={  # sense='sqlite'
            'sqlite': {
                'db': 'my_store.db',
            }
        })

        self.assertEqual(StoreFactory.sense(context), 'sqlite')

    def test_get_memory(self):

        store = StoreFactory.get(type='memory')
        self.assertTrue(isinstance(store, MemoryStore))

        store = StoreFactory.get(type='memory', context='c', weird='w')
        with self.assertRaises(AttributeError):
            self.assertEqual(store.context, 'c')
        with self.assertRaises(AttributeError):
            self.assertEqual(store.weird, 'w')

    def test_get_sqlite(self):

        bot = ShellBot()
        store = StoreFactory.get(type='sqlite')
        self.assertTrue(isinstance(store, SqliteStore))

    def test_get_unknown(self):

        with self.assertRaises(ValueError):
            store = StoreFactory.get(type='*unknown', ex_token='b', ex_ears='c')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
