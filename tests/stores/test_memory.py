#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context
from shellbot.stores import MemoryStore


class MemoryStoreTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        store = MemoryStore()
        self.assertEqual(str(store.values), "{}")

    def test_on_init(self):

        logging.info('***** on_init')

        class MyMemoryStore(MemoryStore):

            def on_init(self, more=None, **kwargs):
                self.more = more

        store = MyMemoryStore(more='more', weird='weird')
        self.assertEqual(store.more, 'more')
        with self.assertRaises(AttributeError):
            self.assertEqual(store.weird, 'weird')

    def test__set(self):

        logging.info('***** _set')

        store = MemoryStore()

        self.assertEqual(store._get('sca.lar'), None)
        store._set('sca.lar', 'test')
        self.assertEqual(store._get('sca.lar'), 'test')

        self.assertEqual(store._get('list'), None)
        store._set('list', ['hello', 'world'])
        self.assertEqual(store._get('list'), ['hello', 'world'])

        self.assertEqual(store._get('dict'), None)
        store._set('dict', {'hello': 'world'})
        self.assertEqual(store._get('dict'), {'hello': 'world'})

    def test__get(self):

        logging.info('***** _get')

        store = MemoryStore()

        # undefined key
        self.assertEqual(store._get('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(store.recall('hello', whatever), whatever)

        # set the key
        store._set('hello', 'world')
        self.assertEqual(store._get('hello'), 'world')

        # default value is meaningless when key has been set
        store.remember('hello', 'world')
        self.assertEqual(store.recall('hello', 'whatever'), 'world')

        # except when set to None
        store._set('special', None)
        self.assertEqual(store._get('special'), None)
        self.assertEqual(store.recall('special', []), [])

    def test__clear(self):

        logging.info('***** _clear')

        store = MemoryStore()

        # set the key and then forget it
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

        store = MemoryStore()

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
