#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context

my_context = Context()


class ContextTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
        }

        context = Context(settings)
        self.assertEqual(context.get('bot.name'), 'testy')
        self.assertEqual(context.get('bot.version'), '17.4.1')

    def test_init_filter(self):

        context = Context(filter=lambda x, y : x + '...')
        context.apply({'my.var': 'my value'})
        context.check('my.var', filter=True)
        self.assertEqual(context.get('my.var'), 'my value...')

    def test_apply(self):

        self.assertEqual(my_context.get('general.port'), None)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'spark.room': 'title',
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
        }

        my_context.apply(settings)

        self.assertEqual(my_context.get('general.DEBUG'), True)
        self.assertEqual(my_context.get('spark.CISCO_SPARK_BTTN_BOT'),
                         'who_knows')
        self.assertEqual(my_context.get('spark.room'), 'title')
        self.assertEqual(my_context.get('server.port'), 80)
        self.assertEqual(my_context.get('server.url'), 'http://www.acme.com/')

    def test_clear(self):

        self.assertEqual(my_context.get('general.port'), None)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'spark.room': 'title',
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
        }

        my_context.apply(settings)

        self.assertEqual(my_context.get('general.DEBUG'), True)
        self.assertEqual(my_context.get('spark.CISCO_SPARK_BTTN_BOT'),
                         'who_knows')
        self.assertEqual(my_context.get('spark.room'), 'title')
        self.assertEqual(my_context.get('server.port'), 80)
        self.assertEqual(my_context.get('server.url'), 'http://www.acme.com/')

        my_context.clear()

        self.assertEqual(my_context.get('general.DEBUG'), None)
        self.assertEqual(my_context.get('spark.CISCO_SPARK_BTTN_BOT'), None)
        self.assertEqual(my_context.get('spark.room'), None)
        self.assertEqual(my_context.get('server.port'), None)
        self.assertEqual(my_context.get('server.url'), None)

    def test_is_empty(self):

        self.assertTrue(my_context.is_empty)

        # set a key
        my_context.set('hello', 'world')
        self.assertEqual(my_context.get('hello'), 'world')
        self.assertFalse(my_context.is_empty)

        my_context.clear()
        self.assertTrue(my_context.is_empty)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'spark.room': 'title',
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
        }

        my_context.apply(settings)
        self.assertFalse(my_context.is_empty)

    def test_check(self):

        self.assertEqual(my_context.get('spark.room'), None)

        settings = {
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        }

        my_context.apply(settings)

        my_context.check('spark.room', is_mandatory=True)
        self.assertEqual(my_context.get('spark.room'), 'My preferred room')

        my_context.check('spark.team')
        self.assertEqual(my_context.get('spark.team'), 'Anchor team')

        my_context.check('spark.*not*present')   # will be set to None
        self.assertEqual(my_context.get('spark.*not*present'), None)

        my_context.check('spark.absent_list', default=[])
        self.assertEqual(my_context.get('spark.absent_list'), [])

        my_context.check('spark.absent_dict', default={})
        self.assertEqual(my_context.get('spark.absent_dict'), {})

        my_context.check('spark.absent_text', default='*born')
        self.assertEqual(my_context.get('spark.absent_text'), '*born')

        # is_mandatory is useless if default is set
        my_context.check('spark.*not*present',
                         default='*born',
                         is_mandatory=True)
        self.assertEqual(my_context.get('spark.*not*present'), '*born')

        # missing key
        with self.assertRaises(KeyError):
            my_context.check('spark.*unknown*key*',
                             is_mandatory=True)

        # validate implies is_mandatory
        with self.assertRaises(KeyError):
            my_context.check('spark.*unknown*key*',
                             validate=lambda line: True)

        # filter does imply is_mandatory
        with self.assertRaises(KeyError):
            my_context.check('spark.*unknown*key*',
                             filter=True)

        my_context.check('spark.webhook',
                         validate=lambda line: line.startswith('http'))
        self.assertEqual(my_context.get('spark.webhook'),
                         "http://73a1e282.ngrok.io")

        with self.assertRaises(ValueError):
            my_context.check('spark.token',
                             validate=lambda line: len(line) == 32)
        self.assertEqual(my_context.get('spark.token'),
                         'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY')

        my_context.check('spark.personal_token')
        self.assertEqual(my_context.get('spark.personal_token'),
                         '$MY_FUZZY_SPARK_TOKEN')

        my_context.check('spark.personal_token', filter=True)  # warning in log
        self.assertEqual(my_context.get('spark.personal_token'),
                         None)

        my_context.apply(settings)

        os.environ['MY_FUZZY_SPARK_TOKEN'] = ''
        my_context.check('spark.personal_token', filter=True)
        self.assertEqual(my_context.get('spark.personal_token'), '')

        my_context.check('spark.fuzzy_token')
        self.assertEqual(my_context.get('spark.fuzzy_token'),
                         '$MY_FUZZY_SPARK_TOKEN')

        os.environ['MY_FUZZY_SPARK_TOKEN'] = 'hello'
        my_context.check('spark.fuzzy_token', filter=True)
        self.assertEqual(my_context.get('spark.fuzzy_token'), 'hello')

    def test__filter(self):

        self.assertEqual(Context._filter(None), None)

        self.assertEqual(Context._filter(''), '')

        self.assertEqual(Context._filter('ZLOGQ0OVGlZWU1NmYtyY'),
                         'ZLOGQ0OVGlZWU1NmYtyY')

        if os.environ.get('PATH') is not None:
            self.assertTrue(Context._filter('$PATH') != '$PATH')

        Context._filter('$TOTALLY*UNKNOWN*HERE')  # warning in log

    def test_has(self):

        my_context.apply({
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        # undefined prefix
        self.assertFalse(my_context.has('hello'))

        # top-level prefix
        self.assertTrue(my_context.has('spark'))

        # 2-level prefix
        self.assertTrue(my_context.has('spark.team'))

        # undefined 2-level prefix
        self.assertFalse(my_context.has('.token'))

    def test_getter(self):

        # undefined key
        self.assertEqual(my_context.get('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(my_context.get('hello', whatever), whatever)

        # set a key
        my_context.set('hello', 'world')
        self.assertEqual(my_context.get('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(my_context.get('hello', 'whatever'), 'world')

        # except when set to None
        my_context.set('special', None)
        self.assertEqual(my_context.get('special', []), [])

    def test_unicode(self):

        my_context.set('hello', 'world')
        self.assertEqual(my_context.get('hello'), 'world')
        self.assertEqual(my_context.get(u'hello'), 'world')

        my_context.set('hello', u'wôrld')
        self.assertEqual(my_context.get('hello'), u'wôrld')

        my_context.set(u'hello', u'wôrld')
        self.assertEqual(my_context.get(u'hello'), u'wôrld')

    def test_increment(self):

        self.assertEqual(my_context.get('gauge'), None)
        value = my_context.increment('gauge')
        self.assertEqual(value, 1)

        my_context.set('gauge', 'world')
        self.assertEqual(my_context.get('gauge'), 'world')
        value = my_context.increment('gauge')
        self.assertEqual(value, 1)

    def test_decrement(self):

        self.assertEqual(my_context.get('gauge'), None)
        value = my_context.decrement('gauge')
        self.assertEqual(value, -1)

        my_context.set('gauge', 'world')
        self.assertEqual(my_context.get('gauge'), 'world')
        value = my_context.decrement('gauge')
        self.assertEqual(value, -1)

    def test_gauge(self):

        # undefined key
        self.assertEqual(my_context.get('gauge'), None)

        # see if type mismatch would create an error
        my_context.set('gauge', 'world')
        self.assertEqual(my_context.get('gauge'), 'world')

        # increment and decrement the counter
        value = my_context.increment('gauge')
        self.assertEqual(value, 1)
        self.assertEqual(my_context.get('gauge'), 1)

        self.assertEqual(my_context.decrement('gauge', 2), -1)

        self.assertEqual(my_context.increment('gauge', 4), 3)
        self.assertEqual(my_context.decrement('gauge', 10), -7)
        self.assertEqual(my_context.increment('gauge', 27), 20)
        self.assertEqual(my_context.get('gauge'), 20)

        # default value is meaningless when key has been set
        self.assertEqual(my_context.get('gauge', 'world'), 20)

        # reset the gauge
        my_context.set('gauge', 123)
        self.assertEqual(my_context.get('gauge'), 123)

    def test_concurrency(self):

        from multiprocessing import Process
        import random
        import time

        def worker(id, context):
            for i in range(4):
                r = random.random()
                time.sleep(r)
                value = context.increment('gauge')
                logging.info('worker %d:counter=%d' % (id, value))
            logging.info('worker %d:done' % id)

        logging.info('Creating a counter')
        self.counter = Context()

        logging.info('Launching incrementing workers')
        workers = []
        for i in range(4):
            p = Process(target=worker, args=(i, self.counter,))
            p.start()
            workers.append(p)

        logging.info('Waiting for worker threads')
        for p in workers:
            p.join()

        logging.info('Counter: %d' % self.counter.get('gauge'))
        self.assertEqual(self.counter.get('gauge'), 16)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
