#!/usr/bin/env python

import colorlog
import unittest
import logging
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context


class ContextTests(unittest.TestCase):

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

    def test_init(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
        }

        context = Context(settings)
        self.assertEqual(context.get('bot.name'), 'testy')
        self.assertEqual(context.get('bot.version'), '17.4.1')

    def test_store(self):

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
        self.assertEqual(context.get('hello', whatever), 'world')

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
