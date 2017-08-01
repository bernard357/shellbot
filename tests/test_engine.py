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

from shellbot import Context, Engine, ShellBot, MachineFactory
from shellbot.spaces import Space, LocalSpace, SparkSpace


def clear_env(name):
    try:
        os.environ.pop(name)
    except KeyError:
        pass


class FakeBot(object):
    def __init__(self, engine=None,channel_id=None):
        self.engine = engine
        self.id = channel_id if channel_id else '*bot'
        self.store = self.engine.build_store(id)

    def bond(self):
        pass

    def on_enter(self):
        pass


class MyCounter(object):
    def __init__(self, name='counter'):
        self.name = name
        self.count = 0
    def on_bond(self, bot):
        logging.info('{}.on_bond'.format(self.name))
        self.count += 1
    def on_dispose(self):
        logging.info('{}.on_dispose'.format(self.name))
        self.count += 1
    def __del__(self):
        logging.info('(Deleting {})'.format(self.name))


class MyUpdater(object):
    def __init__(self, id):
        self.id = id


class MyUpdaterFactory(object):
    def get_updater(self, id):
        return MyUpdater(id)


class EngineTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context,
                             mouth=Queue())
        self.space = LocalSpace(context=self.context)
        self.engine.space = self.space


    def tearDown(self):
        del self.space
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** init ***')

        engine = Engine(context=self.context)

        self.assertEqual(engine.context, self.context)
        self.assertTrue(engine.mouth is None)
        self.assertTrue(engine.speaker is not None)
        self.assertTrue(engine.ears is None)
        self.assertTrue(engine.listener is not None)
        self.assertTrue(engine.fan is None)
        self.assertTrue(engine.observer is not None)
        self.assertTrue(engine.registered is not None)
        self.assertEqual(engine.bots, {})
        self.assertFalse(engine.space is None)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertEqual(engine.driver, ShellBot)
        self.assertEqual(engine.machine_factory, None)
        self.assertEqual(engine.updater_factory, None)

        del engine

        engine = Engine(context=self.context,
                        type='local',
                        mouth='m',
                        ears='e',
                        fan='f')

        self.assertEqual(engine.context, self.context)
        self.assertEqual(engine.mouth, 'm')
        self.assertTrue(engine.speaker is not None)
        self.assertEqual(engine.ears, 'e')
        self.assertTrue(engine.listener is not None)
        self.assertEqual(engine.fan, 'f')
        self.assertTrue(engine.observer is not None)
        self.assertTrue(engine.registered is not None)
        self.assertEqual(engine.bots, {})
        self.assertTrue(engine.space is not None)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertEqual(engine.driver, ShellBot)
        self.assertEqual(engine.machine_factory, None)
        self.assertEqual(engine.updater_factory, None)

        del engine

        engine = Engine(context=self.context,
                        space=self.space,
                        mouth='m',
                        ears='e',
                        fan='f')

        self.assertEqual(engine.context, self.context)
        self.assertEqual(engine.mouth, 'm')
        self.assertTrue(engine.speaker is not None)
        self.assertEqual(engine.ears, 'e')
        self.assertTrue(engine.listener is not None)
        self.assertEqual(engine.fan, 'f')
        self.assertTrue(engine.observer is not None)
        self.assertTrue(engine.registered is not None)
        self.assertEqual(engine.bots, {})
        self.assertEqual(engine.space, self.space)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertEqual(engine.driver, ShellBot)
        self.assertEqual(engine.machine_factory, None)
        self.assertEqual(engine.updater_factory, None)

        del engine

        engine = Engine(context=self.context,
                        driver=FakeBot,
                        machine_factory=MachineFactory,
                        updater_factory=MyUpdaterFactory,)

        self.assertEqual(engine.context, self.context)
        self.assertEqual(engine.mouth, None)
        self.assertTrue(engine.speaker is not None)
        self.assertEqual(engine.ears, None)
        self.assertTrue(engine.listener is not None)
        self.assertTrue(engine.fan is None)
        self.assertTrue(engine.observer is not None)
        self.assertTrue(engine.registered is not None)
        self.assertEqual(engine.bots, {})
        self.assertTrue(engine.space is not None)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertEqual(engine.driver, FakeBot)
        self.assertEqual(engine.machine_factory, MachineFactory)
        self.assertEqual(engine.updater_factory, MyUpdaterFactory)

        self.context.apply({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        engine = Engine(context=self.context)
        self.assertEqual(engine.name, 'testy')
        self.assertEqual(engine.version, '17.4.1')

        del engine

    def test_configure(self):

        logging.info('*** configure ***')

        self.engine.configure({})
        self.assertEqual(self.engine.space.ears, self.engine.ears)
        self.assertTrue(self.engine.list_factory is not None)

        self.engine.context.clear()
        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'space': {
                'title': 'space name',
                'participants': ['joe.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.no.where',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }
        self.engine.configure(settings)
        self.assertEqual(self.engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(self.engine.get('space.title'), 'space name')
        self.assertEqual(self.engine.get('space.participants'),
                         ['joe.bar@acme.com'])
        self.assertEqual(self.engine.get('server.url'), 'http://to.no.where')
        self.assertEqual(self.engine.get('server.hook'), '/hook')

        self.engine.context.clear()
        self.engine.configure_from_path(os.path.dirname(os.path.abspath(__file__))
                                      + '/test_settings/regular.yaml')
        self.assertEqual(self.engine.get('bot.on_enter'), 'How can I help you?')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye for now')
        self.assertEqual(self.engine.get('local.title'), 'Support channel')
        self.assertEqual(self.engine.get('local.participants'),
                         ['joe.bar@acme.com', 'super.support@help.org'])
        self.assertEqual(self.engine.get('server.url'), None)
        self.assertEqual(self.engine.get('server.hook'), None)
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), None)

        items = [x for x in self.engine.list_factory.get_list('SupportTeam')]
        self.assertEqual(items, ['service.desk@acme.com', 'supervisor@brother.mil'])

        items = [x for x in self.engine.list_factory.get_list('*unknown*list')]
        self.assertEqual(items, [])

        names = self.engine.list_factory.list_commands()
        self.assertEqual(sorted(names), ['SupportTeam'])

    def test_configuration_2(self):

        logging.info('*** configure 2 ***')

        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'space': {
                'title': 'Support channel',
            },

            'server': {
                'url': 'http://to.nowhere/',
                'trigger': '/trigger',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        clear_env('CHANNEL_DEFAULT_PARTICIPANTS')
        context = Context(settings)
        engine = Engine(context=context, configure=True)
        self.assertEqual(engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(engine.get('space.title'), 'Support channel')
        self.assertEqual(engine.get('space.participants'), None)
        self.assertEqual(engine.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(engine.get('server.hook'), '/hook')
        self.assertEqual(engine.get('server.trigger'), '/trigger')
        self.assertEqual(engine.get('server.binding'), None)
        self.assertEqual(engine.get('server.port'), 8080)

    def test_configure_default(self):

        logging.info('*** configure with default values ***')

        clear_env("BOT_BANNER_TEXT")
        clear_env("BOT_BANNER_CONTENT")
        clear_env("BOT_BANNER_FILE")
        clear_env("BOT_ON_ENTER")
        clear_env("BOT_ON_EXIT")
        clear_env("CHAT_ROOM_TITLE")
        clear_env("CHANNEL_DEFAULT_PARTICIPANTS")
        clear_env("CISCO_SPARK_BOT_TOKEN")
        clear_env("SERVER_URL")
        self.engine.configure()

#        logging.debug(self.engine.context.values)

        self.assertEqual(self.engine.get('bot.banner.text'), None)
        self.assertEqual(self.engine.get('bot.banner.content'), None)
        self.assertEqual(self.engine.get('bot.banner.file'), None)

        self.assertEqual(self.engine.get('bot.on_enter'), None)
        self.assertEqual(self.engine.get('bot.on_exit'), None)

        self.assertEqual(self.engine.get('space.title'), 'Collaboration space')
        self.assertEqual(self.engine.get('space.participants'), None)
        self.assertEqual(self.engine.get('space.unknown'), None)

        self.assertEqual(self.engine.get('server.url'), '$SERVER_URL')
        self.assertEqual(self.engine.get('server.hook'), '/hook')
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), 8080)

        self.assertEqual(self.engine.space.ears, self.engine.ears)
        self.assertTrue(self.engine.bus is not None)
        self.assertTrue(self.engine.publisher is not None)

    def test_configure_environment(self):

        logging.info('*** configure from the environment ***')

        os.environ["BOT_BANNER_TEXT"] = 'some text'
        os.environ["BOT_BANNER_CONTENT"] = 'some content'
        os.environ["BOT_BANNER_FILE"] = 'some link'
        os.environ["BOT_ON_ENTER"] = 'Hello!'
        os.environ["BOT_ON_EXIT"] = 'Bye!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support channel'
        os.environ["CHANNEL_DEFAULT_PARTICIPANTS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'
        self.engine.configure()

#        logging.debug(self.engine.context.values)

        self.assertEqual(self.engine.get('bot.banner.text'), 'some text')
        self.assertEqual(self.engine.get('bot.banner.content'), 'some content')
        self.assertEqual(self.engine.get('bot.banner.file'), 'some link')

        self.assertEqual(self.engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye!')

        self.assertEqual(self.engine.get('space.title'), 'Support channel')
        self.assertEqual(self.engine.get('space.participants'), 'foo.bar@acme.com')
        self.assertEqual(self.engine.get('space.unknown'), None)

        self.assertEqual(self.engine.get('server.url'), '$SERVER_URL')
        self.assertEqual(self.engine.get('server.hook'), '/hook')
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), 8080)

    def test_get(self):

        logging.info('*** get ***')

        os.environ["BOT_ON_ENTER"] = 'Hello!'
        os.environ["BOT_ON_EXIT"] = 'Bye!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support channel'
        os.environ["CHANNEL_DEFAULT_PARTICIPANTS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'

        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'space': {
                'title': '$CHAT_ROOM_TITLE',
            },

            'server': {
                'url': '$SERVER_URL',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        self.engine.configure(settings=settings)

        self.assertEqual(self.engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(self.engine.get('space.title'), 'Support channel')
        self.assertEqual(self.engine.get('space.participants'), 'foo.bar@acme.com')

        self.assertEqual(self.engine.get('space.unknown'), None)

        self.assertEqual(self.engine.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(self.engine.get('server.hook'), '/hook')
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), 8080)

    def test_set(self):

        logging.info('*** set ***')

        self.engine.set('hello', 'world')
        self.assertEqual(self.engine.get('hello'), 'world')
        self.assertEqual(self.engine.get(u'hello'), 'world')

        self.engine.set('hello', u'wôrld')
        self.assertEqual(self.engine.get('hello'), u'wôrld')

        self.engine.set(u'hello', u'wôrld')
        self.assertEqual(self.engine.get(u'hello'), u'wôrld')

    def test_name(self):

        logging.info('*** name ***')
        self.assertEqual(self.engine.name, 'Shelly')

    def test_version(self):

        logging.info('*** version ***')
        self.assertEqual(self.engine.version, '*unknown*')

    def test_register(self):

        logging.info('*** register ***')

        with self.assertRaises(AttributeError):
            self.engine.register('*unknown*event', lambda : 'ok')
        with self.assertRaises(AttributeError):
            self.engine.register('bond', lambda : 'ok')
        with self.assertRaises(AttributeError):
            self.engine.register('dispose', lambda : 'ok')

        counter = MyCounter('counter #1')
        with self.assertRaises(AssertionError):
            self.engine.register(None, counter)
        with self.assertRaises(AssertionError):
            self.engine.register('', counter)
        with self.assertRaises(AssertionError):
            self.engine.register(1.2, counter)

        self.engine.register('bond', counter)
        self.engine.register('dispose', counter)

        with self.assertRaises(AttributeError):
            self.engine.register('start', counter)
        with self.assertRaises(AttributeError):
            self.engine.register('stop', counter)
        with self.assertRaises(AttributeError):
            self.engine.register('*unknown*event', counter)

        self.engine.register('bond', MyCounter('counter #2'))

        class AllEvents(object):
            def on_bond(self, bot):
                pass
            def on_dispose(self):
                pass
            def on_start(self):
                pass
            def on_stop(self):
                pass
            def on_message(self):
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
        self.engine.register('bond', all_events)
        self.engine.register('dispose', all_events)
        self.engine.register('start', all_events)
        self.engine.register('stop', all_events)
        self.engine.register('message', all_events)
        self.engine.register('join', all_events)
        self.engine.register('leave', all_events)
        self.engine.register('enter', all_events)
        self.engine.register('exit', all_events)
        self.engine.register('inbound', all_events)
        self.engine.register('some_custom_event', all_events)

        self.assertEqual(len(self.engine.registered['bond']), 3)
        self.assertEqual(len(self.engine.registered['dispose']), 2)
        self.assertEqual(len(self.engine.registered['start']), 1)
        self.assertEqual(len(self.engine.registered['stop']), 1)
        self.assertEqual(len(self.engine.registered['message']), 1)
        self.assertEqual(len(self.engine.registered['join']), 1)
        self.assertEqual(len(self.engine.registered['leave']), 1)
        self.assertEqual(len(self.engine.registered['enter']), 1)
        self.assertEqual(len(self.engine.registered['exit']), 1)
        self.assertEqual(len(self.engine.registered['inbound']), 1)
        self.assertEqual(len(self.engine.registered['some_custom_event']), 1)

    def test_dispatch(self):

        logging.info('*** dispatch ***')

        counter = MyCounter('counter #1')
        self.engine.register('bond', counter)
        self.engine.register('dispose', counter)

        self.engine.register('bond', MyCounter('counter #2'))
        self.engine.register('dispose', MyCounter('counter #3'))

        class AllEvents(object):
            def __init__(self):
                self.events = []
            def on_bond(self, bot):
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
        self.engine.register('bond', all_events)
        self.engine.register('dispose', all_events)
        self.engine.register('start', all_events)
        self.engine.register('stop', all_events)
        self.engine.register('message', all_events)
        self.engine.register('join', all_events)
        self.engine.register('leave', all_events)
        self.engine.register('enter', all_events)
        self.engine.register('exit', all_events)
        self.engine.register('inbound', all_events)
        self.engine.register('some_custom_event', all_events)

        self.engine.dispatch('bond', bot='*dummy')
        self.engine.dispatch('dispose')
        self.engine.dispatch('start')
        self.engine.dispatch('stop')
        self.engine.dispatch('message', received='*void')
        self.engine.dispatch('join', received='*void')
        self.engine.dispatch('leave', received='*void')
        self.engine.dispatch('enter', received='*void')
        self.engine.dispatch('exit', received='*void')
        self.engine.dispatch('inbound', received='*void')
        self.engine.dispatch('some_custom_event', data='*data')

        with self.assertRaises(AssertionError):
            self.engine.dispatch('*unknown*event')

        self.assertEqual(counter.count, 2)
        self.assertEqual(all_events.events,
                         ['bond',
                          'dispose',
                          'start',
                          'stop',
                          'message',
                          'join',
                          'leave',
                          'enter',
                          'exit',
                          'inbound',
                          'some_custom_event'])

    def test_load_commands(self):

        logging.info('*** load_commands ***')

        with mock.patch.object(self.engine.shell,
                               'load_commands',
                               return_value=None) as mocked:
            self.engine.load_commands(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_load_command(self):

        logging.info('*** load_command ***')

        with mock.patch.object(self.engine.shell,
                               'load_command',
                               return_value=None) as mocked:
            self.engine.load_command('a')
            mocked.assert_called_with('a')

    def test_hook(self):

        logging.info('*** hook ***')

        self.context.set('server.url', 'http://here.you.go:123')
        server = mock.Mock()
        with mock.patch.object(self.engine.space,
                               'register',
                               return_value=None) as mocked:

            self.engine.hook(server=server)
            self.assertFalse(mocked.called)

            self.context.set('server.binding', '0.0.0.0')
            self.engine.hook(server=server)
            mocked.assert_called_with(hook_url='http://here.you.go:123/hook')

    def test_get_hook(self):

        logging.info('*** get_hook ***')

        self.context.set('server.url', 'http://here.you.go:123')
        self.assertEqual(self.engine.get_hook(), self.engine.space.webhook)

    def test_run(self):

        logging.info('*** run ***')

        engine = Engine(context=self.context)
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

        engine = Engine(context=self.context)
        engine.space=LocalSpace(engine=engine)

        engine.start_processes = mock.Mock()
        engine.on_start = mock.Mock()

        engine.start()
        self.assertTrue(engine.ears is not None)
        self.assertTrue(engine.mouth is not None)
        self.assertTrue(engine.start_processes.called)
        self.assertTrue(engine.on_start.called)

    def test_static(self):

        logging.info('*** static test ***')

        self.engine.configure()
        self.context.set('bus.address', 'tcp://127.0.0.1:6666')
        self.engine.listener.DEFER_DURATION = 0.0
        self.engine.publisher.DEFER_DURATION = 0.0
        self.engine.start()
        self.engine.stop()

        self.assertEqual(self.engine.get('listener.counter', 0), 0)
        self.assertEqual(self.engine.get('speaker.counter', 0), 0)

    def test_bond(self):

        logging.info("*** bond")

        self.space.delete = mock.Mock()

        channel = self.engine.bond(title=None)
        self.assertEqual(channel.id, '*local')
        self.assertEqual(channel.title, 'Collaboration space')

        channel = self.engine.bond(title='')
        self.assertEqual(channel.id, '*local')
        self.assertEqual(channel.title, 'Collaboration space')

        channel = self.engine.bond(title='hello world')
        self.assertEqual(channel.id, '*local')
        self.assertEqual(channel.title, 'hello world')

        self.assertFalse(self.space.delete.called)
        channel = self.engine.bond(reset=True)
        self.assertTrue(self.space.delete.called)

        self.space.add_participants = mock.Mock()
        self.engine.dispatch = mock.Mock()

        with mock.patch.object(self.space,
                               'get_by_title',
                               return_value=None) as mocked:
            self.engine.bond(
                title='my title',
                participants=['c', 'd'],
            )
            mocked.assert_called_with(title='my title')
            self.space.add_participants.assert_called_with(id='*local', persons=['c', 'd'])

        self.space.configure(settings={
            'space': {
                'title': 'Another title',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
            }
        })
        with mock.patch.object(self.space,
                               'get_by_title',
                               return_value=None) as mocked:
            self.engine.bond()
            mocked.assert_called_with(title='Another title')
            self.space.add_participants.assert_called_with(
                id='*local',
                persons=['alan.droit@azerty.org', 'bob.nard@support.tv'])

    def test_enumerate_bots(self):

        logging.info('*** enumerate_bots ***')

        self.engine.bots = {
            '123': FakeBot(self.engine, '123'),
            '456': FakeBot(self.engine, '456'),
            '789': FakeBot(self.engine, '789'),
        }

        for bot in self.engine.enumerate_bots():
            self.assertTrue(bot.id in ['123', '456', '789'])

    def test_get_bot(self):

        logging.info('*** get_bot ***')

        self.engine.bots = {
            '123': FakeBot(self.engine, '123'),
            '456': FakeBot(self.engine, '456'),
            '789': FakeBot(self.engine, '789'),
        }

        bot = self.engine.get_bot('123')
        self.assertEqual(bot.id, '123')
        self.assertEqual(bot, self.engine.bots['123'])

        bot = self.engine.get_bot('456')
        self.assertEqual(bot.id, '456')
        self.assertEqual(bot, self.engine.bots['456'])

        bot = self.engine.get_bot('789')
        self.assertEqual(bot.id, '789')
        self.assertEqual(bot, self.engine.bots['789'])

        with mock.patch.object(self.engine,
                               'build_bot',
                               return_value=FakeBot(self.engine, '*bot')) as mocked:

            bot = self.engine.get_bot()
            self.assertEqual(bot.id, '*bot')
            self.assertTrue('*bot' in self.engine.bots.keys())

    def test_build_bot(self):

        logging.info('*** build_bot ***')

        self.engine.context.apply(self.engine.DEFAULT_SETTINGS)
        self.engine.bots = {}

        bot = self.engine.build_bot('123', FakeBot)
        self.assertEqual(bot.id, '123')
        bot.store.remember('a', 'b')
        self.assertEqual(bot.store.recall('a'), 'b')

        bot = self.engine.build_bot('456', FakeBot)
        self.assertEqual(bot.id, '456')
        bot.store.remember('c', 'd')
        self.assertEqual(bot.store.recall('a'), None)
        self.assertEqual(bot.store.recall('c'), 'd')

        bot = self.engine.build_bot('789', FakeBot)
        self.assertEqual(bot.id, '789')
        bot.store.remember('e', 'f')
        self.assertEqual(bot.store.recall('a'), None)
        self.assertEqual(bot.store.recall('c'), None)
        self.assertEqual(bot.store.recall('e'), 'f')

    def test_on_build(self):

        logging.info('*** on_build ***')

        bot = ShellBot(engine=self.engine)
        self.engine.on_build(bot)

    def test_build_store(self):

        logging.info('*** build_store ***')

        store_1 = self.engine.build_store('123')
        store_1.append('names', 'Alice')
        store_1.append('names', 'Bob')
        self.assertEqual(store_1.recall('names'), ['Alice', 'Bob'])

        store_2 = self.engine.build_store('456')
        store_2.append('names', 'Chloe')
        store_2.append('names', 'David')
        self.assertEqual(store_2.recall('names'), ['Chloe', 'David'])

        self.assertEqual(store_1.recall('names'), ['Alice', 'Bob'])
        store_2.forget()
        self.assertEqual(store_1.recall('names'), ['Alice', 'Bob'])
        self.assertEqual(store_2.recall('names'), None)

    def test_initialize_store(self):

        logging.info('*** initialize_store ***')

        settings = {'bot.store': {'planets': ['Uranus', 'Mercury']}}
        self.engine.context.apply(settings)
        print(self.engine.get('bot.store'))
        bot = self.engine.build_bot('123', FakeBot)
        self.assertEqual(bot.store.recall('planets'), ['Uranus', 'Mercury'])

    def test_build_machine(self):

        logging.info('*** build_machine ***')

        bot = ShellBot(engine=self.engine)
        machine = self.engine.build_machine(bot)

        previous = self.engine.machine_factory
        self.engine.machine_factory = MachineFactory(
            module='shellbot.machines.base',
            name='Machine')
        machine = self.engine.build_machine(bot)
        self.engine.machine_factory = previous

    def test_build_updater(self):

        logging.info('*** build_updater ***')

        updater = self.engine.build_updater('*id')
        self.assertEqual(updater, None)

        self.engine.updater_factory = MyUpdaterFactory()
        updater = self.engine.build_updater('*id')
        self.assertEqual(updater.id, '*id')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
