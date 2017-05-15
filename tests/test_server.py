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

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Server
from shellbot.routes import Route, Notify, Text, Wrap


class ServerTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** Init test ***')

        server = Server()
        self.assertTrue(server.context is not None)
        self.assertTrue(server.httpd is not None)

        context = Context()
        server = Server(context=context, httpd='h')
        self.assertEqual(server.context, context)
        self.assertEqual(server.httpd, 'h')

    def test_configuration(self):

        logging.info('*** Configuration test ***')

        settings = {
            'server': {
                'port': 8888,
                'debug': True,
            },
        }

        context = Context(settings)
        server = Server(context=context)
        self.assertEqual(server.context.get('server.binding'), None)
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

        context = Context(settings)
        server = Server(context=context, check=True)
        self.assertEqual(server.context.get('server.binding'), '0.0.0.0')
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

        settings = {
            'server': {
                'binding': '1.2.3.4',
                'port': 8888,
                'debug': True,
            },
        }

        server = Server()
        server.configure(settings)
        self.assertEqual(server.context.get('server.binding'), '1.2.3.4')
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

        server = Server(Context(settings))
        self.assertEqual(server.context.get('server.binding'), '1.2.3.4')
        self.assertEqual(server.context.get('server.port'), 8888)
        self.assertEqual(server.context.get('server.debug'), True)

    def test_routes(self):

        logging.info('*** Routes test ***')

        hello = Route(route='/hello')
        world = Route(route='/world')

        server = Server()
        server.add_routes([hello, world])
        self.assertEqual(server.routes, ['/hello', '/world'])
        self.assertEqual(server.route('/hello'), hello)
        self.assertEqual(server.route('/world'), world)

        server = Server(routes=[hello, world])
        self.assertEqual(server.routes, ['/hello', '/world'])
        self.assertEqual(server.route('/hello'), hello)
        self.assertEqual(server.route('/world'), world)

    def test_route(self):

        logging.info('*** Route test ***')

        route = Route(route='/hello')

        server = Server()
        server.add_route(route)
        self.assertEqual(server.routes, ['/hello'])
        self.assertEqual(server.route('/hello'), route)

        server = Server(route=route)
        self.assertEqual(server.routes, ['/hello'])
        self.assertEqual(server.route('/hello'), route)

    def test_run(self):

        logging.info('*** Run test ***')

        class FakeHttpd(object):
            def run(self, **kwargs):
                pass

        server = Server(httpd=FakeHttpd())
        server.run()

    def test_text(self):

        logging.info('*** Text test***')

        route = Text(route='/hello', page='Hello, world!')

        server = Server(route=route)

        test = TestApp(server.httpd)
        r = test.get('/hello')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('Hello, world!')

    def test_notify(self):

        logging.info('*** Notify test***')

        queue = Queue()
        route = Notify(route='/notify', queue=queue, notification='hello!')

        server = Server(route=route)

        test = TestApp(server.httpd)
        r = test.get('/notify')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('OK')
        time.sleep(0.1)
        self.assertEqual(queue.get_nowait(), 'hello!')

    def test_wrap(self):

        logging.info('*** Wrap test***')

        context = Context()

        class Callable(object):
            def __init__(self, context):
                self.context = context

            def hook(self, **kwargs):
                self.context.set('signal', 'wrapped!')
                return 'OK'

        callable = Callable(context)

        route = Wrap(context=context,
                     route='/wrapper',
                     callable=callable.hook)

        server = Server(context=context, route=route)

        self.assertEqual(context.get('signal'), None)

        test = TestApp(server.httpd)
        r = test.get('/wrapper')
        self.assertEqual(r.status, '200 OK')
        r.mustcontain('OK')

        self.assertEqual(context.get('signal'), 'wrapped!')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
