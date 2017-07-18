#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
from multiprocessing import Queue
import sys
import time
from webtest import TestApp

from shellbot import Context, Server
from shellbot.routes import Route, Notifier, Text, Wrapper

my_context = Context()


class ServerTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** Init test ***')

        server = Server()
        self.assertTrue(server.context is not None)
        self.assertTrue(server.httpd is not None)

        server = Server(context=my_context, httpd='h')
        self.assertEqual(server.context, my_context)
        self.assertEqual(server.httpd, 'h')

    def test_configuration(self):

        logging.info('*** Configuration test ***')

        settings = {
            'server': {
                'binding': '1.2.3.4',
                'port': 8888,
                'debug': True,
            },
        }

        server = Server(context=my_context)
        self.assertEqual(server.context.get('server.binding'), None)
        self.assertEqual(server.context.get('server.port'), None)
        self.assertEqual(server.context.get('server.debug'), None)
        server.configure(settings)
        self.assertEqual(server.context.get('server.binding'), '1.2.3.4')
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

        context = Context(settings)
        server = Server(context=context)
        self.assertEqual(server.context.get('server.binding'), '1.2.3.4')
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

    def test_routes(self):

        logging.info('*** Routes test ***')

        hello = Route(route='/hello')
        world = Route(route='/world')

        server = Server(context=my_context)
        server.add_routes([hello, world])
        self.assertEqual(server.routes, ['/hello', '/world'])
        self.assertEqual(server.route('/hello'), hello)
        self.assertEqual(server.route('/world'), world)

        server = Server(context=my_context, routes=[hello, world])
        self.assertEqual(server.routes, ['/hello', '/world'])
        self.assertEqual(server.route('/hello'), hello)
        self.assertEqual(server.route('/world'), world)

    def test_route(self):

        logging.info('*** Route test ***')

        route = Route(route='/hello')

        server = Server(context=my_context)
        server.add_route(route)
        self.assertEqual(server.routes, ['/hello'])
        self.assertEqual(server.route('/hello'), route)

        server = Server(context=my_context, route=route)
        self.assertEqual(server.routes, ['/hello'])
        self.assertEqual(server.route('/hello'), route)

    def test_run(self):

        logging.info('*** Run test ***')

        class FakeHttpd(object):
            def run(self, **kwargs):
                pass

        server = Server(context=my_context, httpd=FakeHttpd())
        server.run()

    def test_text(self):

        logging.info('*** Text test***')

        route = Text(route='/hello', page='Hello, world!')

        server = Server(context=my_context, route=route)

        test = TestApp(server.httpd)
        r = test.get('/hello')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Hello, world!')

    def test_notifier(self):

        logging.info('*** Notify test***')

        queue = Queue()
        route = Notifier(route='/notify', queue=queue, notification='hello!')

        server = Server(context=my_context, route=route)

        test = TestApp(server.httpd)
        r = test.get('/notify')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('OK')
        time.sleep(0.1)
        self.assertEqual(queue.get_nowait(), 'hello!')

    def test_wrapper(self):

        logging.info('*** Wrap test***')

        class Callable(object):
            def __init__(self, context):
                self.context = context

            def hook(self, **kwargs):
                self.context.set('signal', 'wrapped!')
                return 'OK'

        callable = Callable(my_context)

        route = Wrapper(context=my_context,
                        route='/wrapper',
                        callable=callable.hook)

        server = Server(context=my_context, route=route)

        self.assertEqual(my_context.get('signal'), None)

        test = TestApp(server.httpd)
        r = test.get('/wrapper')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('OK')

        self.assertEqual(my_context.get('signal'), 'wrapped!')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
