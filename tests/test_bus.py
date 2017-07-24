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
        self.assertTrue(self.bus.zmq_context is not None)

    def test_bus_check(self):

        logging.info(u"***** bus/check")

        self.bus.check()
        self.assertEqual(self.context.get('bus.address'), self.bus.DEFAULT_ADDRESS)
        self.assertTrue(self.bus.zmq_context is not None)

    def test_bus_subscribe(self):

        logging.info(u"***** bus/subscribe")

        subscriber = self.bus.subscribe('topic')

    def test_bus_publish(self):

        logging.info(u"***** bus/publish")

        publisher = self.bus.publish()

    def test_subscriber_init(self):

        logging.info(u"***** subscriber/init")

        subscriber =  Subscriber(socket='s')
        self.assertEqual(subscriber.socket, 's')

    def test_subscriber_get(self):

        logging.info(u"***** subscriber/get")

        subscriber =  self.bus.subscribe('dummy')
        with mock.patch.object(subscriber.socket,
                               'recv',
                               return_value='topic {"hello": "world"}') as mocked:

            message = subscriber.get()
            self.assertEqual(message, {u'hello': u'world'})

    def test_publisher_init(self):

        logging.info(u"***** publisher/init")

        publisher =  Publisher(socket='s')
        self.assertEqual(publisher.socket, 's')

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
            publisher.put('topic', None)

        with self.assertRaises(AssertionError):
            publisher.put('topic', '')

        with mock.patch.object(publisher.socket,
                               'send') as mocked:

            publisher.put('topic', 'message')
            mocked.assert_called_with('topic "message"')

            publisher.put(['topic'], 'message')
            mocked.assert_called_with('topic "message"')



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
