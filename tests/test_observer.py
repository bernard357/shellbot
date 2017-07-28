#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
from threading import Timer
import time

from shellbot import Context, Engine, SpaceFactory
from shellbot.observer import Observer

my_engine = Engine(fan=Queue())


class ObserverTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        observer = Observer(engine=my_engine)

        observer.start()

        observer.join(0.1)
        if observer.is_alive():
            logging.info('Stopping observer')
            my_engine.set('general.switch', 'off')
            observer.join()

        self.assertFalse(observer.is_alive())
        self.assertEqual(my_engine.get('observer.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        items = ['hello', 'world']
        for item in items:
            my_engine.fan.put(item)
        my_engine.fan.put(None)

        observer = Observer(engine=my_engine)

        observer.run()

        with self.assertRaises(Exception):
            engine.fan.get_nowait()

    def test_start(self):

        logging.info("*** start")

        my_engine.fan.put('ping')

        my_engine.set('general.switch', 'on')
        my_engine.set('observer.counter', 0) # do not wait for run()

        observer = Observer(engine=my_engine)
        observer.start()
        while True:
            counter = my_engine.get('observer.counter', 0)
            if counter > 0:
                logging.info("- observer.counter > 0")
                break
        my_engine.set('general.switch', 'off')
        observer.join()

        self.assertTrue(my_engine.get('observer.counter') > 0)

    def test_run(self):

        logging.info("*** run")

        my_engine.observer.process = mock.Mock(side_effect=Exception('TEST'))
        my_engine.fan.put(('dummy'))
        my_engine.fan.put(None)
        my_engine.observer.run()
        self.assertEqual(my_engine.get('observer.counter'), 0)

        my_engine.observer = Observer(engine=my_engine)
        my_engine.observer.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        my_engine.fan.put(('dummy'))
        my_engine.observer.run()
        self.assertEqual(my_engine.get('observer.counter'), 0)

    def test_run_wait(self):

        logging.info("*** run/wait while empty")

        my_engine.observer.NOT_READY_DELAY = 0.01
        my_engine.set('general.switch', 'on')
        my_engine.observer.start()

        t = Timer(0.1, my_engine.fan.put, ['ping'])
        t.start()

        time.sleep(0.2)
        my_engine.set('general.switch', 'off')
        my_engine.observer.join()

    def test_process(self):

        logging.info('*** process ***')

        observer = Observer(engine=my_engine)

        observer.process('hello world')



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
