#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
from multiprocessing import Manager, Process, Queue
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Engine
from shellbot.spaces import Space, LocalSpace, SparkSpace

my_context = Context()
my_engine = Engine(context=my_context,
                   mouth=Queue())
my_space = LocalSpace(engine=my_engine)
my_engine.space = my_space


class MyCounter(object):
    def __init__(self, name='counter'):
        self.name = name
        self.count = 0
    def on_bond(self):
        logging.info('{}.on_bond'.format(self.name))
        self.count += 1
    def on_dispose(self):
        logging.info('{}.on_dispose'.format(self.name))
        self.count += 1
    def __del__(self):
        logging.info('(Deleting {})'.format(self.name))


class EngineTests(unittest.TestCase):

    def tearDown(self):
        my_engine.context.clear()
        my_engine.subscribed = {
            'bond': [],       # connected to a space
            'dispose': [],    # space will be destroyed
            'start': [],      # starting bot services
            'stop': [],       # stopping bot services
            'message': [],    # message received (with message)
            'attachment': [], # attachment received (with attachment)
            'join': [],       # joining a space (with person)
            'leave': [],      # leaving a space (with person)
            'enter': [],      # invited to a space (for the bot)
            'exit': [],       # kicked off from a space (for the bot)
            'inbound': [],    # other event received from space (with event)
        }
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** init ***')

        engine = Engine(context=my_context)

        self.assertEqual(engine.context, my_context)
        self.assertTrue(engine.space is None)
        self.assertTrue(engine.mouth is None)
        self.assertTrue(engine.inbox is None)
        self.assertTrue(engine.ears is None)
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.speaker is not None)
        self.assertTrue(engine.worker is not None)
        self.assertTrue(engine.listener is not None)

        engine = Engine(context=my_context,
                        type='local',
                        mouth='m',
                        inbox='i',
                        ears='e')

        self.assertEqual(engine.context, my_context)
        self.assertTrue(engine.space is not None)
        self.assertEqual(engine.mouth, 'm')
        self.assertEqual(engine.inbox, 'i')
        self.assertEqual(engine.ears, 'e')
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.speaker is not None)
        self.assertTrue(engine.worker is not None)
        self.assertTrue(engine.listener is not None)

        engine = Engine(context=my_context,
                        space=my_space,
                        mouth='m',
                        inbox='i',
                        ears='e')

        self.assertEqual(engine.context, my_context)
        self.assertEqual(engine.space, my_space)
        self.assertEqual(engine.mouth, 'm')
        self.assertEqual(engine.inbox, 'i')
        self.assertEqual(engine.ears, 'e')
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.speaker is not None)
        self.assertTrue(engine.worker is not None)
        self.assertTrue(engine.listener is not None)

        context = Context({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        engine = Engine(context=context)
        self.assertEqual(engine.name, 'testy')
        self.assertEqual(engine.version, '17.4.1')

    def test_configure(self):

        logging.info('*** configure ***')

        my_engine.configure({})

        my_engine.context.clear()
        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'local': {
                'title': 'space name',
                'moderators': ['foo.bar@acme.com'],
                'participants': ['joe.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.no.where',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }
        my_engine.configure(settings)
        self.assertEqual(my_engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(my_engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(my_engine.get('local.title'), 'space name')
        self.assertEqual(my_engine.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(my_engine.get('local.participants'),
                         ['joe.bar@acme.com'])
        self.assertEqual(my_engine.get('server.url'), 'http://to.no.where')
        self.assertEqual(my_engine.get('server.hook'), '/hook')

        my_engine.context.clear()
        my_engine.configure_from_path(os.path.dirname(os.path.abspath(__file__))
                                      + '/test_settings/regular.yaml')
        self.assertEqual(my_engine.get('bot.on_enter'), 'How can I help you?')
        self.assertEqual(my_engine.get('bot.on_exit'), 'Bye for now')
        self.assertEqual(my_engine.get('local.title'), 'Support room')
        self.assertEqual(my_engine.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(my_engine.get('local.participants'),
                         ['joe.bar@acme.com', 'super.support@help.org'])
        self.assertEqual(my_engine.get('server.url'), None)
        self.assertEqual(my_engine.get('server.hook'), None)
        self.assertEqual(my_engine.get('server.binding'), None)
        self.assertEqual(my_engine.get('server.port'), None)

    def test_configuration_2(self):

        logging.info('*** configure 2 ***')

        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'local': {
                'title': 'Support room',
                'moderators': ['foo.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.nowhere/',
                'trigger': '/trigger',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        context = Context(settings)
        engine = Engine(context=context, configure=True)
        self.assertEqual(engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(engine.get('local.title'), 'Support room')
        self.assertEqual(engine.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(engine.get('local.participants'), [])
        self.assertEqual(engine.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(engine.get('server.hook'), '/hook')
        self.assertEqual(engine.get('server.trigger'), '/trigger')
        self.assertEqual(engine.get('server.binding'), None)
        self.assertEqual(engine.get('server.port'), 8080)

    def test_configure_default(self):

        logging.info('*** configure/default configuration ***')

        logging.debug("- default configuration is not interpreted")

        os.environ["BOT_ON_ENTER"] = 'Hello!'
        os.environ["BOT_ON_EXIT"] = 'Bye!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'
        my_engine.configure()

        self.assertEqual(my_engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(my_engine.get('bot.on_exit'), 'Bye!')

        self.assertEqual(my_engine.get('spark.room'), '$CHAT_ROOM_TITLE')
        self.assertEqual(my_engine.get('spark.moderators'), '$CHAT_ROOM_MODERATORS')
        self.assertEqual(my_engine.get('spark.participants'), None)
        self.assertEqual(my_engine.get('spark.token'), None)

        self.assertEqual(my_engine.get('server.url'), '$SERVER_URL')
        self.assertEqual(my_engine.get('server.hook'), '/hook')
        self.assertEqual(my_engine.get('server.binding'), None)
        self.assertEqual(my_engine.get('server.port'), 8080)

        my_engine.context.clear()
        os.environ['CHAT_ROOM_TITLE'] = 'Notifications'
        engine = Engine(context=my_context, settings=None, configure=True, fan='f')
        self.assertEqual(engine.get('spark.room'), 'Notifications')

    def test_get(self):

        logging.info('*** get ***')

        os.environ["BOT_ON_ENTER"] = 'Hello!'
        os.environ["BOT_ON_EXIT"] = 'Bye!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'

        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'local': {
                'title': '$CHAT_ROOM_TITLE',
                'moderators': '$CHAT_ROOM_MODERATORS',
            },

            'server': {
                'url': '$SERVER_URL',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        my_engine.configure(settings=settings)

        self.assertEqual(my_engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(my_engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(my_engine.get('local.title'), 'Support room')
        self.assertEqual(my_engine.get('local.moderators'),
                         'foo.bar@acme.com')
        self.assertEqual(my_engine.get('local.participants'), [])

        self.assertEqual(my_engine.get('local.token'), None)

        self.assertEqual(my_engine.get('server.url'), '$SERVER_URL')
        self.assertEqual(my_engine.get('server.hook'), '/hook')
        self.assertEqual(my_engine.get('server.binding'), None)
        self.assertEqual(my_engine.get('server.port'), 8080)

    def test_set(self):

        logging.info('*** set ***')

        my_engine.set('hello', 'world')
        self.assertEqual(my_engine.get('hello'), 'world')
        self.assertEqual(my_engine.get(u'hello'), 'world')

        my_engine.set('hello', u'wôrld')
        self.assertEqual(my_engine.get('hello'), u'wôrld')

        my_engine.set(u'hello', u'wôrld')
        self.assertEqual(my_engine.get(u'hello'), u'wôrld')

    def test_subscribe(self):

        logging.info('*** subscribe ***')

        with self.assertRaises(AttributeError):
            my_engine.subscribe('*unknown*event', lambda : 'ok')
        with self.assertRaises(AttributeError):
            my_engine.subscribe('bond', lambda : 'ok')
        with self.assertRaises(AttributeError):
            my_engine.subscribe('dispose', lambda : 'ok')

        counter = MyCounter('counter #1')
        with self.assertRaises(AssertionError):
            my_engine.subscribe(None, counter)
        with self.assertRaises(AssertionError):
            my_engine.subscribe('', counter)
        with self.assertRaises(AssertionError):
            my_engine.subscribe(1.2, counter)

        my_engine.subscribe('bond', counter)
        my_engine.subscribe('dispose', counter)

        with self.assertRaises(AttributeError):
            my_engine.subscribe('start', counter)
        with self.assertRaises(AttributeError):
            my_engine.subscribe('stop', counter)
        with self.assertRaises(AttributeError):
            my_engine.subscribe('*unknown*event', counter)

        my_engine.subscribe('bond', MyCounter('counter #2'))

        class AllEvents(object):
            def on_bond(self):
                pass
            def on_dispose(self):
                pass
            def on_start(self):
                pass
            def on_stop(self):
                pass
            def on_message(self):
                pass
            def on_attachment(self):
                pass
            def on_join(self):
                pass
            def on_leave(self):
                pass
            def on_enter(self):
                pass
            def on_exit(self):
                pass
            def on_inbound(self):
                pass
            def on_some_custom_event(self):
                pass

        all_events = AllEvents()
        my_engine.subscribe('bond', all_events)
        my_engine.subscribe('dispose', all_events)
        my_engine.subscribe('start', all_events)
        my_engine.subscribe('stop', all_events)
        my_engine.subscribe('message', all_events)
        my_engine.subscribe('attachment', all_events)
        my_engine.subscribe('join', all_events)
        my_engine.subscribe('leave', all_events)
        my_engine.subscribe('enter', all_events)
        my_engine.subscribe('exit', all_events)
        my_engine.subscribe('inbound', all_events)
        my_engine.subscribe('some_custom_event', all_events)

        self.assertEqual(len(my_engine.subscribed['bond']), 3)
        self.assertEqual(len(my_engine.subscribed['dispose']), 2)
        self.assertEqual(len(my_engine.subscribed['start']), 1)
        self.assertEqual(len(my_engine.subscribed['stop']), 1)
        self.assertEqual(len(my_engine.subscribed['message']), 1)
        self.assertEqual(len(my_engine.subscribed['attachment']), 1)
        self.assertEqual(len(my_engine.subscribed['join']), 1)
        self.assertEqual(len(my_engine.subscribed['leave']), 1)
        self.assertEqual(len(my_engine.subscribed['enter']), 1)
        self.assertEqual(len(my_engine.subscribed['exit']), 1)
        self.assertEqual(len(my_engine.subscribed['inbound']), 1)
        self.assertEqual(len(my_engine.subscribed['some_custom_event']), 1)

    def test_dispatch(self):

        logging.info('*** dispatch ***')

        counter = MyCounter('counter #1')
        my_engine.subscribe('bond', counter)
        my_engine.subscribe('dispose', counter)

        my_engine.subscribe('bond', MyCounter('counter #2'))
        my_engine.subscribe('dispose', MyCounter('counter #3'))

        class AllEvents(object):
            def __init__(self):
                self.events = []
            def on_bond(self):
                self.events.append('bond')
            def on_dispose(self):
                self.events.append('dispose')
            def on_start(self):
                self.events.append('start')
            def on_stop(self):
                self.events.append('stop')
            def on_message(self, received):
                assert received == '*void'
                self.events.append('message')
            def on_attachment(self, received):
                assert received == '*void'
                self.events.append('attachment')
            def on_join(self, received):
                assert received == '*void'
                self.events.append('join')
            def on_leave(self, received):
                assert received == '*void'
                self.events.append('leave')
            def on_enter(self, received):
                assert received == '*void'
                self.events.append('enter')
            def on_exit(self, received):
                assert received == '*void'
                self.events.append('exit')
            def on_inbound(self, received):
                assert received == '*void'
                self.events.append('inbound')
            def on_some_custom_event(self, data):
                assert data == '*data'
                self.events.append('some_custom_event')

        all_events = AllEvents()
        my_engine.subscribe('bond', all_events)
        my_engine.subscribe('dispose', all_events)
        my_engine.subscribe('start', all_events)
        my_engine.subscribe('stop', all_events)
        my_engine.subscribe('message', all_events)
        my_engine.subscribe('attachment', all_events)
        my_engine.subscribe('join', all_events)
        my_engine.subscribe('leave', all_events)
        my_engine.subscribe('enter', all_events)
        my_engine.subscribe('exit', all_events)
        my_engine.subscribe('inbound', all_events)
        my_engine.subscribe('some_custom_event', all_events)

        my_engine.dispatch('bond')
        my_engine.dispatch('dispose')
        my_engine.dispatch('start')
        my_engine.dispatch('stop')
        my_engine.dispatch('message', received='*void')
        my_engine.dispatch('attachment', received='*void')
        my_engine.dispatch('join', received='*void')
        my_engine.dispatch('leave', received='*void')
        my_engine.dispatch('enter', received='*void')
        my_engine.dispatch('exit', received='*void')
        my_engine.dispatch('inbound', received='*void')
        my_engine.dispatch('some_custom_event', data='*data')

        with self.assertRaises(AssertionError):
            my_engine.dispatch('*unknown*event')

        self.assertEqual(counter.count, 2)
        self.assertEqual(all_events.events,
                         ['bond',
                          'dispose',
                          'start',
                          'stop',
                          'message',
                          'attachment',
                          'join',
                          'leave',
                          'enter',
                          'exit',
                          'inbound',
                          'some_custom_event'])

    def test_load_commands(self):

        logging.info('*** load_commands ***')

        with mock.patch.object(my_engine.shell,
                               'load_commands',
                               return_value=None) as mocked:
            my_engine.load_commands(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_hook(self):

        logging.info('*** hook ***')

        my_context.set('server.url', 'http://here.you.go:123')
        server = mock.Mock()
        with mock.patch.object(my_engine.space,
                               'register',
                               return_value=None) as mocked:

            my_engine.hook(server=server)
            self.assertFalse(mocked.called)

            my_context.set('server.binding', '0.0.0.0')
            my_engine.hook(server=server)
            mocked.assert_called_with(hook_url='http://here.you.go:123/hook')

    def test_get_hook(self):

        logging.info('*** get_hook ***')

        my_context.set('server.url', 'http://here.you.go:123')
        self.assertEqual(my_engine.get_hook(), my_engine.space.webhook)

    def test_run(self):

        logging.info('*** run ***')

        engine = Engine(context=my_context)
        engine.space=LocalSpace(engine=engine)

        engine.start = mock.Mock()
        engine.space.run = mock.Mock()

        engine.run()
        self.assertTrue(engine.start.called)
        self.assertTrue(engine.space.run.called)

        class MyServer(object):
            def __init__(self, engine):
                self.engine = engine

            def add_route(self, route, **kwargs):
                pass

            def run(self):
                self.engine.set("has_been_ran", True)

        server = MyServer(engine=engine)
        engine.run(server=server)
        self.assertTrue(engine.get("has_been_ran"))

    def test_start(self):

        logging.info('*** start ***')

        engine = Engine(context=my_context)
        engine.space=LocalSpace(engine=engine)

        engine.start_processes = mock.Mock()
        engine.on_start = mock.Mock()

        engine.start()
        self.assertTrue(engine.ears is not None)
        self.assertTrue(engine.inbox is not None)
        self.assertTrue(engine.mouth is not None)
        self.assertTrue(engine.start_processes.called)
        self.assertTrue(engine.on_start.called)

    def test_static(self):

        logging.info('*** static test ***')

        my_engine.start()
        time.sleep(0.1)
        my_engine.stop()

        self.assertEqual(my_engine.get('listener.counter', 0), 0)
        self.assertEqual(my_engine.get('worker.counter', 0), 0)
        self.assertEqual(my_engine.get('speaker.counter', 0), 0)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
