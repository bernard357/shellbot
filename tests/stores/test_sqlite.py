#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import os
import random
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot
from shellbot.stores import SqliteStore


my_bot = ShellBot()
my_db_name = os.path.dirname(os.path.abspath(__file__)) + '/../local/store.db'


class SqliteStoreTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        store = SqliteStore(bot=my_bot)

    def test_check(self):

        logging.info('***** check')

        store = SqliteStore(bot=my_bot)
        store.check()

    def test_bond(self):

        logging.info('***** bond')

        store = SqliteStore(bot=my_bot, db=my_db_name)

        store.bond()

        store.bond(id='*123')

    def test__set(self):

        logging.info('***** _set')

        store = SqliteStore(bot=my_bot, db=my_db_name)
        store.bond()

        choices = ['hello', 'world', 'how', 'are', 'you']
        value = random.choice(choices)
        store._set('sca.lar', value)
        self.assertEqual(store._get('sca.lar'), value)
        store._set('sca.lar', None)
        self.assertEqual(store._get('sca.lar'), None)

        self.assertEqual(store._get('list'), None)
        value = store.to_text(['hello', 'world'])
        store._set('list', value)
        self.assertEqual(store._get('list'), value)
        store._set('list', None)
        self.assertEqual(store._get('list'), None)

        self.assertEqual(store._get('dict'), None)
        value = store.to_text({'hello': 'world'})
        store._set('dict', value)
        self.assertEqual(store._get('dict'), value)
        store._set('dict', None)
        self.assertEqual(store._get('dict'), None)

    def test__get(self):

        logging.info('***** _get')

        store = SqliteStore(bot=my_bot, db=my_db_name)
        store.bond()

        key = '*no*chance*it*exists'

        # undefined key
        self.assertEqual(store._get(key), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(store.recall(key, whatever), whatever)

        # set the key
        store._set(key, 'hello world')
        self.assertEqual(store._get(key), 'hello world')

        # default value is meaningless when key has been set
        store.remember(key, 'hello world')
        self.assertEqual(store.recall(key, 'whatever'), 'hello world')

        # forget the ky
        store._set(key, None)
        self.assertEqual(store._get(key), None)
        self.assertEqual(store.recall(key), None)

    def test__clear(self):

        logging.info('***** _clear')

        store = SqliteStore(bot=my_bot, db=my_db_name)
        store.bond()

        # set a key and then forget it
        store._set('hello', 'world')
        self.assertEqual(store._get('hello'), 'world')
        store._clear('hello')
        self.assertEqual(store._get('hello'), None)

        # set multiple keys and then forget all of them
        store._set('hello', 'world')
        store._set('bunny', "What'up, Doc?")
        self.assertEqual(store._get('hello'), 'world')
        self.assertEqual(store._get('bunny'), "What'up, Doc?")
        store._clear(key=None)
        self.assertEqual(store._get('hello'), None)
        self.assertEqual(store._get('bunny'), None)

    def test_unicode(self):

        logging.info('***** unicode')

        store = SqliteStore(bot=my_bot, db=my_db_name)
        store.bond()

        store._set('hello', 'world')
        self.assertEqual(store._get('hello'), 'world')
        self.assertEqual(store._get(u'hello'), 'world')

        store._set('hello', u'wôrld')
        self.assertEqual(store._get('hello'), u'wôrld')

        store._set(u'hello', u'wôrld')
        self.assertEqual(store._get(u'hello'), u'wôrld')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
