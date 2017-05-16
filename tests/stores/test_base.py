#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
from multiprocessing import Manager, Process
import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot
from shellbot.stores import Store


my_bot = ShellBot()


class MyStore(Store):

    def on_init(self, **kwargs):
        self.values = Manager().dict()

    def _set(self, key, value):
        self.values[key] = value

    def _get(self, key):
        return self.values.get(key, None)

    def _clear(self, key):
        if key in (None, ''):
            self.values.clear()
        else:
            self.values[key] = None


class StoreTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        store = Store()
        self.assertEqual(store.bot, None)
        self.assertTrue(store.lock is not None)

        store = Store(bot=my_bot)
        self.assertEqual(store.bot, my_bot)

    def test_on_init(self):

        logging.info('***** on_init')

        class MyStore(Store):

            def on_init(self, more=None, **kwargs):
                self.more = more

        store = MyStore(more='more', weird='weird')
        self.assertEqual(store.more, 'more')
        with self.assertRaises(AttributeError):
            self.assertEqual(store.weird, 'weird')

    def test_check(self):

        logging.info('***** check')

        store = Store(bot=my_bot)
        store.check()

    def test_bond(self):

        logging.info('***** bond')

        store = Store(bot=my_bot)
        store.bond()

        store.bond(id='*123')

    def test_to_text(self):

        logging.info('***** to_text')

        store = Store()

        self.assertEqual(store.to_text('text'),
                         '"text"')

        self.assertEqual(store.to_text(['hello', 'world']),
                         '["hello", "world"]')

        self.assertEqual(store.to_text({'hello': 'world'}),
                         '{"hello": "world"}')

    def test_from_text(self):

        logging.info('***** from_text')

        store = Store()

        value = 'text'
        self.assertEqual(store.from_text(store.to_text(value)), value)

        value = ['hello', 'world', 123, 4.56, ['another', 'list']]
        self.assertEqual(store.from_text(store.to_text(value)), value)

        value = {'hello': 'world'}
        self.assertEqual(store.from_text(store.to_text(value)), value)

    def test_remember(self):

        logging.info('***** remember')

        store = MyStore()

        self.assertEqual(store.recall('sca.lar'), None)
        store.remember('sca.lar', 'test')
        self.assertEqual(store.recall('sca.lar'), 'test')

        self.assertEqual(store.recall('list'), None)
        store.remember('list', ['hello', 'world'])
        self.assertEqual(store.recall('list'), ['hello', 'world'])

        self.assertEqual(store.recall('dict'), None)
        store.remember('dict', {'hello': 'world'})
        self.assertEqual(store.recall('dict'), {'hello': 'world'})

    def test__set(self):

        logging.info('***** _set')

        store = Store()

        with self.assertRaises(NotImplementedError):
            store._set('sca.lar', 'test')

    def test_recall(self):

        logging.info('***** recall')

        store = MyStore()

        # undefined key
        self.assertEqual(store.recall('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(store.recall('hello', whatever), whatever)

        # set the key
        store.remember('hello', 'world')
        self.assertEqual(store.recall('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(store.recall('hello', 'whatever'), 'world')

        # except when set to None
        store.remember('special', None)
        self.assertEqual(store.recall('special', []), [])

    def test_unicode(self):

        logging.info('***** unicode')

        store = MyStore()

        store.remember('hello', 'world')
        self.assertEqual(store.recall('hello'), 'world')
        self.assertEqual(store.recall(u'hello'), 'world')

        store.remember('hello', u'wôrld')
        self.assertEqual(store.recall('hello'), u'wôrld')

        store.remember(u'hello', u'wôrld')
        self.assertEqual(store.recall(u'hello'), u'wôrld')

    def test__get(self):

        logging.info('***** _get')

        store = Store()

        with self.assertRaises(NotImplementedError):
            store._get('sca.lar')

    def test_forget(self):

        logging.info('***** forget')

        store = MyStore()

        # set the key and then forget it
        store.remember('hello', 'world')
        self.assertEqual(store.recall('hello'), 'world')
        store.forget('hello')
        self.assertEqual(store.recall('hello'), None)

        # set multiple keys and then forget all of them
        store.remember('hello', 'world')
        store.remember('bunny', "What'up, Doc?")
        self.assertEqual(store.recall('hello'), 'world')
        self.assertEqual(store.recall('bunny'), "What'up, Doc?")
        store.forget()
        self.assertEqual(store.recall('hello'), None)
        self.assertEqual(store.recall('bunny'), None)

    def test__clear(self):

        logging.info('***** _clear')

        store = Store()

        with self.assertRaises(NotImplementedError):
            store._clear('sca.lar')

    def test_gauge(self):

        logging.info('***** increment & decrement')

        store = MyStore()

        # undefined key
        self.assertEqual(store.recall('gauge'), None)

        # type mismatch should not be an error
        store.remember('gauge', 'world')
        self.assertEqual(store.recall('gauge'), 'world')

        # increment and decrement the counter
        value = store.increment('gauge')
        self.assertEqual(value, 1)
        self.assertEqual(store.recall('gauge'), 1)
        self.assertEqual(store.decrement('gauge', 2), -1)
        self.assertEqual(store.increment('gauge', 4), 3)
        self.assertEqual(store.decrement('gauge', 10), -7)
        self.assertEqual(store.increment('gauge', 27), 20)
        self.assertEqual(store.recall('gauge'), 20)

        # default value is meaningless when key has been set
        self.assertEqual(store.recall('gauge', 'world'), 20)

        # reset the gauge
        store.remember('gauge', 123)
        self.assertEqual(store.recall('gauge'), 123)
        value = store.increment('gauge')
        self.assertEqual(value, 124)

        # a brand new gauge
        value = store.increment('another gauge')
        self.assertEqual(value, 1)

        # a brand new gauge
        value = store.decrement('a gauge')
        self.assertEqual(value, -1)

    def test_append(self):

        logging.info('***** append')

        store = MyStore()

        store.append('famous', 'hello, world')
        store.append('famous', "What'up, Doc?")
        self.assertEqual(store.recall('famous'),
                         ['hello, world', "What'up, Doc?"])

    def test_update(self):

        logging.info('***** update')

        store = MyStore()

        store.update('input', 'PO#', '1234A')
        store.update('input', 'description', 'part does not fit')
        self.assertEqual(store.recall('input'),
                         {u'PO#': u'1234A', u'description': u'part does not fit'})

    def test_concurrency(self):

        logging.info('***** concurrency')

        def worker(id, store):
            for i in range(4):
                r = random.random()
                time.sleep(r)
                value = store.increment('gauge')
                logging.info('worker %d:counter=%d' % (id, value))
            logging.info('worker %d:done' % id)

        logging.info('Creating a counter')

        store = MyStore()

        logging.info('Launching incrementing workers')
        workers = []
        for i in range(4):
            p = Process(target=worker, args=(i, store,))
            p.start()
            workers.append(p)

        logging.info('Waiting for worker threads')
        for p in workers:
            p.join()

        logging.info('Counter: %d' % store.recall('gauge'))
        self.assertEqual(store.recall('gauge'), 16)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
