#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import json
import logging
import mock
from multiprocessing import Process
import sys
import time

from shellbot import Context
from shellbot.bus import Bus, Subscriber, Publisher


class BusTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.context.set('general.switch', 'on')
        self.context.set('bus.address', 'tcp://127.0.0.1:6666')
        self.bus = Bus(context=self.context)

    def tearDown(self):
        del self.bus
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_bus_init(self):

        logging.info(u"***** bus/init")

        self.assertEqual(self.bus.DEFAULT_ADDRESS, 'tcp://127.0.0.1:5555')
        self.assertEqual(self.bus.context, self.context)

    def test_bus_check(self):

        logging.info(u"***** bus/check")

        self.context.set('bus.address', None)
        self.bus.check()
        self.assertEqual(self.context.get('bus.address'), self.bus.DEFAULT_ADDRESS)

    def test_bus_subscribe(self):

        logging.info(u"***** bus/subscribe")

        with self.assertRaises(AssertionError):
            subscriber = self.bus.subscribe(None)

        with self.assertRaises(AssertionError):
            subscriber = self.bus.subscribe([])

        with self.assertRaises(AssertionError):
            subscriber = self.bus.subscribe(())

        subscriber = self.bus.subscribe('channel')

    def test_bus_publish(self):

        logging.info(u"***** bus/publish")

        publisher = self.bus.publish()

    def test_subscriber_init(self):

        logging.info(u"***** subscriber/init")

        subscriber =  Subscriber(context=self.context, channels='channel')
        self.assertEqual(subscriber.context, self.context)
        self.assertTrue(subscriber.socket is None)

    def test_subscriber_get(self):

        logging.info(u"***** subscriber/get")

        subscriber =  self.bus.subscribe('dummy')
        subscriber.socket = mock.Mock()
        with mock.patch.object(subscriber.socket,
                               'recv',
                               return_value='dummy {"hello": "world"}') as mocked:

            message = subscriber.get()
            self.assertEqual(message, {u'hello': u'world'})

    def test_publisher_init(self):

        logging.info(u"***** publisher/init")

        publisher =  Publisher(context=self.context)
        self.assertEqual(publisher.context, self.context)
        self.assertTrue(publisher.socket is None)

    def test_publisher_run(self):

        logging.info(u"***** publisher/run")

        publisher =  Publisher(context=self.context)

        self.context.set('general.switch', 'off')
        publisher.run()

        self.context.set('general.switch', 'on')
        publisher.put('*weird', '*message')
        publisher.fan.put(None)
        publisher.run()

    def test_publisher_static_test(self):

        logging.info(u"***** publisher/static test")

        publisher = Publisher(context=self.context)
        publisher.DEFER_DURATION = 0.0
        self.context.set('general.switch', 'on')
        publisher.start()

        publisher.join(0.1)
        if publisher.is_alive():
            logging.info('Stopping publisher')
            self.context.set('general.switch', 'off')
            publisher.join()

        self.assertFalse(publisher.is_alive())
        self.assertEqual(self.context.get('publisher.counter', 0), 0)

    def test_publisher_dynamic_test(self):

        logging.info(u"***** publisher/dynamic test")

        publisher = Publisher(context=self.context)
        self.context.set('general.switch', 'on')

        items = [
            ('channel_A', "hello"),
            ('channel_B', "world"),
            ('channel_C', {"hello": "world"}),
        ]

        for (channel, message) in items:
            publisher.put(channel, message)

        publisher.fan.put(None)

        class MySocket(object):
            def __init__(self, context):
                self.context = context

            def send_string(self, item):
                pipe = self.context.get('pipe', [])
                pipe.append(item)
                self.context.set('pipe', pipe)

            def close(self):
                pass

        publisher.socket = MySocket(self.context)
        publisher.run()

        self.assertEqual(self.context.get('publisher.counter', 0), 3)
        self.assertEqual(
            self.context.get('pipe'),
            ['channel_A "hello"', 'channel_B "world"', 'channel_C {"hello": "world"}'])

    def test_publisher_put(self):

        logging.info(u"***** publisher/put")

        publisher = self.bus.publish()

        with self.assertRaises(AssertionError):
            publisher.put(None, 'message')

        with self.assertRaises(AssertionError):
            publisher.put('', 'message')

        with self.assertRaises(AssertionError):
            publisher.put([], 'message')

        with self.assertRaises(AssertionError):
            publisher.put((), 'message')

        with self.assertRaises(AssertionError):
            publisher.put('channel', None)

        with self.assertRaises(AssertionError):
            publisher.put('channel', '')

        with mock.patch.object(publisher.fan,
                               'put') as mocked:

            publisher.put('channel', 'message')
            mocked.assert_called_with('channel "message"')

            publisher.put(['channel'], 'message')
            mocked.assert_called_with('channel "message"')

    def test_life_cycle(self):

        logging.info(u"***** life cycle")

        class Listener(Process):
            def __init__(self, bus):
                Process.__init__(self)
                self.daemon = True
                self.bus = bus

            def run(self):
                subscriber =  self.bus.subscribe('')
                logging.info(u"Starting subscriber")

                while self.bus.context.get('general.switch', 'off') == 'on':

                    message = subscriber.get()
                    if not message:
                        time.sleep(0.001)
                        continue

                    self.bus.context.set('received', message)
                    logging.info(u"- {}".format(message))

                logging.info(u"Stopping subscriber")


        listener = Listener(self.bus)
        listener.start()

        publisher = self.bus.publish()
        publisher.start()

        for value in range(1, 10):
            publisher.put('channel', {'counter': value})
        publisher.fan.put(None)

        publisher.join()
        time.sleep(0.5)
        self.bus.context.set('general.switch', 'off')
        time.sleep(0.5)
        listener.join()

#        self.assertEqual(self.context.get('received'), {'counter': 9})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
