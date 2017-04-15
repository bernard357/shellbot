#!/usr/bin/env python

import colorlog
import unittest
import logging
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context


class ContextTests(unittest.TestCase):

    def test_init(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
        }

        context = Context(settings)
        self.assertEqual(context.get('bot.name'), 'testy')
        self.assertEqual(context.get('bot.version'), '17.4.1')

    def test_apply(self):

        context = Context()

        self.assertEqual(context.get('general.port'), None)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
        }

        context.apply(settings)

        self.assertEqual(context.get('general.DEBUG'), True)
        self.assertEqual(context.get('spark.CISCO_SPARK_BTTN_BOT'), 'who_knows')
        self.assertEqual(context.get('server.port'), 80)
        self.assertEqual(context.get('server.url'), 'http://www.acme.com/')

    def test_parse(self):

        context = Context()

        self.assertEqual(context.get('spark.room'), None)

        settings = {
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'webhook': "http://73a1e282.ngrok.io",
            }
        }

        context.parse(settings, 'spark', 'room', is_mandatory=True)
        self.assertEqual(context.get('spark.room'), 'My preferred room')

        context.parse(settings, 'spark', 'team')
        self.assertEqual(context.get('spark.team'), 'Anchor team')

        context.parse(settings, 'spark', '*not*present')
        self.assertEqual(context.get('spark.*not*present'), None)

        context.parse(settings,
                      'spark',
                      'absent_list',
                      default=[])
        self.assertEqual(context.get('spark.absent_list'), [])

        context.parse(settings,
                      'spark',
                      'absent_dict',
                      default={})
        self.assertEqual(context.get('spark.absent_dict'), {})

        context.parse(settings,
                      'spark',
                      'absent_text',
                      default='*born')
        self.assertEqual(context.get('spark.absent_text'), '*born')

        context.parse(settings,  # is_mandatory is useless if default is set
                      'spark',
                      '*not*present',
                      default='*born',
                      is_mandatory=True)
        self.assertEqual(context.get('spark.*not*present'), '*born')

        with self.assertRaises(KeyError): # missing key
            context.parse(settings,
                          'spark',
                          '*unknown*key*',
                          is_mandatory=True)

        with self.assertRaises(KeyError): # validate implies is_mandatory
            context.parse(settings,
                          'spark',
                          '*unknown*key*',
                          validate=lambda line: True)

        context.parse(settings,
                      'spark',
                      'webhook',
                      validate=lambda line: line.startswith('http'))
        self.assertEqual(context.get('spark.webhook'),
                         "http://73a1e282.ngrok.io")

        with self.assertRaises(ValueError): # present, but not put in context
            context.parse(settings,
                          'spark',
                          'token',
                          validate=lambda line: len(line) == 32)
        self.assertEqual(context.get('spark.token'), None)

    def test_getter(self):

        context = Context()

        # undefined key
        self.assertEqual(context.get('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(context.get('hello', whatever), whatever)

        # set the key
        context.set('hello', 'world')
        self.assertEqual(context.get('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(context.get('hello', 'whatever'), 'world')

        # except when set to None
        context.set('special', None)
        self.assertEqual(context.get('special', []), [])

    def test_gauge(self):

        context = Context()

        # undefined key
        self.assertEqual(context.get('gauge'), None)

        # see if type mismatch would create an error
        context.set('gauge', 'world')
        self.assertEqual(context.get('gauge'), 'world')

        # increment and decrement the counter
        value = context.increment('gauge')
        self.assertEqual(value, 1)
        self.assertEqual(context.get('gauge'), 1)

        self.assertEqual(context.decrement('gauge', 2), -1)

        self.assertEqual(context.increment('gauge', 4), 3)
        self.assertEqual(context.decrement('gauge', 10), -7)
        self.assertEqual(context.increment('gauge', 27), 20)
        self.assertEqual(context.get('gauge'), 20)

        # default value is meaningless when key has been set
        self.assertEqual(context.get('gauge', 'world'), 20)

        # reset the gauge
        context.set('gauge', 123)
        self.assertEqual(context.get('gauge'), 123)

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

    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(asctime)-2s %(log_color)s%(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)

    logging.getLogger('').handlers = []
    logging.getLogger('').addHandler(handler)

    logging.getLogger('').setLevel(level=logging.DEBUG)

    sys.exit(unittest.main())
