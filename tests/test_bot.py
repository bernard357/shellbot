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

from shellbot import Context, ShellBot
from shellbot.spaces import Space, LocalSpace, SparkSpace
from shellbot.stores import MemoryStore

my_context = Context()
my_bot = ShellBot(context=my_context,
                  mouth=Queue(),
                  fan='f')
my_space = LocalSpace(bot=my_bot)
my_bot.space = my_space
my_store = MemoryStore(bot=my_bot)
my_bot.store = my_store

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


class BotTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        my_store.forget()
        my_bot.subscribed = {
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

        bot = ShellBot(context=my_context)

        self.assertEqual(bot.context, my_context)
        self.assertTrue(bot.space is None)
        self.assertTrue(bot.store is None)
        self.assertTrue(bot.mouth is None)
        self.assertTrue(bot.inbox is None)
        self.assertTrue(bot.ears is None)
        self.assertTrue(bot.fan is None)
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.speaker is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

        bot = ShellBot(context=my_context,
                       type='local',
                       mouth='m',
                       inbox='i',
                       ears='e',
                       fan='f',
                       store='s')

        self.assertEqual(bot.context, my_context)
        self.assertTrue(bot.space is not None)
        self.assertEqual(bot.store, 's')
        self.assertEqual(bot.mouth, 'm')
        self.assertEqual(bot.inbox, 'i')
        self.assertEqual(bot.ears, 'e')
        self.assertEqual(bot.fan, 'f')
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.speaker is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

        bot = ShellBot(context=my_context,
                       space=my_space,
                       mouth='m',
                       inbox='i',
                       ears='e',
                       fan='f',
                       store='s')

        self.assertEqual(bot.context, my_context)
        self.assertEqual(bot.space, my_space)
        self.assertEqual(bot.store, 's')
        self.assertEqual(bot.mouth, 'm')
        self.assertEqual(bot.inbox, 'i')
        self.assertEqual(bot.ears, 'e')
        self.assertEqual(bot.fan, 'f')
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.speaker is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

        context = Context({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        bot = ShellBot(context=context)
        self.assertEqual(bot.name, 'testy')
        self.assertEqual(bot.version, '17.4.1')

    def test_configure(self):

        logging.info('*** configure ***')

        my_bot.configure({})

        my_context.clear()
        settings = {

            'bot': {
                'on_start': 'Start!',
                'on_stop': 'Stop!',
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
        my_bot.configure(settings)
        self.assertEqual(my_bot.context.get('bot.on_start'), 'Start!')
        self.assertEqual(my_bot.context.get('bot.on_stop'), 'Stop!')
        self.assertEqual(my_bot.context.get('local.title'), 'space name')
        self.assertEqual(my_bot.context.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(my_bot.context.get('local.participants'),
                         ['joe.bar@acme.com'])
        self.assertEqual(my_bot.context.get('server.url'), 'http://to.no.where')
        self.assertEqual(my_bot.context.get('server.hook'), '/hook')

        my_context.clear()
        my_bot.configure_from_path(os.path.dirname(os.path.abspath(__file__))
                                + '/test_settings/regular.yaml')
        self.assertEqual(my_bot.context.get('bot.on_start'),
                         'How can I help you?')
        self.assertEqual(my_bot.context.get('bot.on_stop'), 'Bye for now')
        self.assertEqual(my_bot.context.get('local.title'), 'Support room')
        self.assertEqual(my_bot.context.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(my_bot.context.get('local.participants'),
                         ['joe.bar@acme.com', 'super.support@help.org'])
        self.assertEqual(my_bot.context.get('server.url'), None)
        self.assertEqual(my_bot.context.get('server.hook'), None)
        self.assertEqual(my_bot.context.get('server.binding'), None)
        self.assertEqual(my_bot.context.get('server.port'), None)

    def test_configuration_2(self):

        logging.info('*** configure 2 ***')

        settings = {

            'bot': {
                'on_start': 'Start!',
                'on_stop': 'Stop!',
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
        bot = ShellBot(context=context, configure=True, fan='f')
        self.assertEqual(bot.context.get('bot.on_start'), 'Start!')
        self.assertEqual(bot.context.get('bot.on_stop'), 'Stop!')
        self.assertEqual(bot.context.get('local.title'), 'Support room')
        self.assertEqual(bot.context.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.context.get('local.participants'), [])
        self.assertEqual(bot.context.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(bot.context.get('server.hook'), '/hook')
        self.assertEqual(bot.context.get('server.trigger'), '/trigger')
        self.assertEqual(bot.context.get('server.binding'), None)
        self.assertEqual(bot.context.get('server.port'), 8080)

    def test_configure_default(self):

        logging.info('*** configure/default configuration ***')

        logging.debug("- default configuration is not interpreted")

        os.environ["BOT_ON_START"] = 'Start!'
        os.environ["BOT_ON_STOP"] = 'Stop!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'
        my_bot.configure()

        self.assertEqual(my_bot.context.get('bot.on_start'), 'Start!')
        self.assertEqual(my_bot.context.get('bot.on_stop'), 'Stop!')

        self.assertEqual(my_bot.context.get('spark.room'), '$CHAT_ROOM_TITLE')
        self.assertEqual(my_bot.context.get('spark.moderators'), '$CHAT_ROOM_MODERATORS')
        self.assertEqual(my_bot.context.get('spark.participants'), None)
        self.assertEqual(my_bot.context.get('spark.token'), None)

        self.assertEqual(my_bot.context.get('server.url'), '$SERVER_URL')
        self.assertEqual(my_bot.context.get('server.hook'), '/hook')
        self.assertEqual(my_bot.context.get('server.binding'), None)
        self.assertEqual(my_bot.context.get('server.port'), 8080)

        my_context.clear()
        os.environ['CHAT_ROOM_TITLE'] = 'Notifications'
        bot = ShellBot(context=my_context, settings=None, configure=True, fan='f')
        self.assertEqual(bot.get('spark.room'), 'Notifications')

    def test_get(self):

        logging.info('*** get ***')

        os.environ["BOT_ON_START"] = 'Start!'
        os.environ["BOT_ON_STOP"] = 'Stop!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'

        settings = {

            'bot': {
                'on_start': '$BOT_ON_START',
                'on_stop': '$BOT_ON_STOP',
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

        my_bot.configure(settings=settings)

        self.assertEqual(my_bot.get('bot.on_start'), 'Start!')
        self.assertEqual(my_bot.get('bot.on_stop'), 'Stop!')
        self.assertEqual(my_bot.get('local.title'), 'Support room')
        self.assertEqual(my_bot.get('local.moderators'),
                         'foo.bar@acme.com')
        self.assertEqual(my_bot.get('local.participants'), [])

        self.assertEqual(my_bot.get('local.token'), None)

        self.assertEqual(my_bot.get('server.url'), '$SERVER_URL')
        self.assertEqual(my_bot.get('server.hook'), '/hook')
        self.assertEqual(my_bot.get('server.binding'), None)
        self.assertEqual(my_bot.get('server.port'), 8080)

    def test_set(self):

        logging.info('*** set ***')

        my_bot.set('hello', 'world')
        self.assertEqual(my_bot.get('hello'), 'world')
        self.assertEqual(my_bot.get(u'hello'), 'world')

        my_bot.set('hello', u'wôrld')
        self.assertEqual(my_bot.get('hello'), u'wôrld')

        my_bot.set(u'hello', u'wôrld')
        self.assertEqual(my_bot.get(u'hello'), u'wôrld')

    def test_subscribe(self):

        logging.info('*** subscribe ***')

        with self.assertRaises(AttributeError):
            my_bot.subscribe('*unknown*event', lambda : 'ok')
        with self.assertRaises(AttributeError):
            my_bot.subscribe('bond', lambda : 'ok')
        with self.assertRaises(AttributeError):
            my_bot.subscribe('dispose', lambda : 'ok')

        counter = MyCounter('counter #1')
        with self.assertRaises(AssertionError):
            my_bot.subscribe(None, counter)
        with self.assertRaises(AssertionError):
            my_bot.subscribe('', counter)
        with self.assertRaises(AssertionError):
            my_bot.subscribe(1.2, counter)
        my_bot.subscribe('bond', counter)
        my_bot.subscribe('dispose', counter)
        with self.assertRaises(AttributeError):
            my_bot.subscribe('start', counter)
        with self.assertRaises(AttributeError):
            my_bot.subscribe('stop', counter)
        with self.assertRaises(AttributeError):
            my_bot.subscribe('*unknown*event', counter)

        my_bot.subscribe('bond', MyCounter('counter #2'))

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
        my_bot.subscribe('bond', all_events)
        my_bot.subscribe('dispose', all_events)
        my_bot.subscribe('start', all_events)
        my_bot.subscribe('stop', all_events)
        my_bot.subscribe('message', all_events)
        my_bot.subscribe('attachment', all_events)
        my_bot.subscribe('join', all_events)
        my_bot.subscribe('leave', all_events)
        my_bot.subscribe('enter', all_events)
        my_bot.subscribe('exit', all_events)
        my_bot.subscribe('inbound', all_events)
        my_bot.subscribe('some_custom_event', all_events)

        self.assertEqual(len(my_bot.subscribed['bond']), 3)
        self.assertEqual(len(my_bot.subscribed['dispose']), 2)
        self.assertEqual(len(my_bot.subscribed['start']), 1)
        self.assertEqual(len(my_bot.subscribed['stop']), 1)
        self.assertEqual(len(my_bot.subscribed['message']), 1)
        self.assertEqual(len(my_bot.subscribed['attachment']), 1)
        self.assertEqual(len(my_bot.subscribed['join']), 1)
        self.assertEqual(len(my_bot.subscribed['leave']), 1)
        self.assertEqual(len(my_bot.subscribed['enter']), 1)
        self.assertEqual(len(my_bot.subscribed['exit']), 1)
        self.assertEqual(len(my_bot.subscribed['inbound']), 1)
        self.assertEqual(len(my_bot.subscribed['some_custom_event']), 1)

    def test_dispatch(self):

        logging.info('*** dispatch ***')

        counter = MyCounter('counter #1')
        my_bot.subscribe('bond', counter)
        my_bot.subscribe('dispose', counter)

        my_bot.subscribe('bond', MyCounter('counter #2'))
        my_bot.subscribe('dispose', MyCounter('counter #3'))

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
        my_bot.subscribe('bond', all_events)
        my_bot.subscribe('dispose', all_events)
        my_bot.subscribe('start', all_events)
        my_bot.subscribe('stop', all_events)
        my_bot.subscribe('message', all_events)
        my_bot.subscribe('attachment', all_events)
        my_bot.subscribe('join', all_events)
        my_bot.subscribe('leave', all_events)
        my_bot.subscribe('enter', all_events)
        my_bot.subscribe('exit', all_events)
        my_bot.subscribe('inbound', all_events)
        my_bot.subscribe('some_custom_event', all_events)

        my_bot.dispatch('bond')
        my_bot.dispatch('dispose')
        my_bot.dispatch('start')
        my_bot.dispatch('stop')
        my_bot.dispatch('message', received='*void')
        my_bot.dispatch('attachment', received='*void')
        my_bot.dispatch('join', received='*void')
        my_bot.dispatch('leave', received='*void')
        my_bot.dispatch('enter', received='*void')
        my_bot.dispatch('exit', received='*void')
        my_bot.dispatch('inbound', received='*void')
        my_bot.dispatch('some_custom_event', data='*data')

        with self.assertRaises(AssertionError):
            my_bot.dispatch('*unknown*event')

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

        with mock.patch.object(my_bot.shell,
                               'load_commands',
                               return_value=None) as mocked:
            my_bot.load_commands(['a', 'b', 'c', 'd'])
            mocked.called

    def test_say(self):

        logging.info('*** say ***')

        message_0 = None
        my_bot.say(message_0)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        message_0 = ''
        my_bot.say(message_0)
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        message_1 = 'hello'
        my_bot.say(message_1)
        self.assertEqual(my_bot.mouth.get(), message_1)

        message_2 = 'world'
        my_bot.say(message_2)
        self.assertEqual(my_bot.mouth.get(), message_2)

        message_3 = 'hello'
        content_3 = 'world'
        my_bot.say(message_3, content=content_3)
        item = my_bot.mouth.get()
        self.assertEqual(item.message, message_3)
        self.assertEqual(item.content, content_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        my_bot.say(message_4, file=file_4)
        item = my_bot.mouth.get()
        self.assertEqual(item.message, message_4)
        self.assertEqual(item.content, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        content_5 = 'world'
        file_5 = 'http://some.server/some/file'
        my_bot.say(message_5, content=content_5, file=file_5)
        item = my_bot.mouth.get()
        self.assertEqual(item.message, message_5)
        self.assertEqual(item.content, content_5)
        self.assertEqual(item.file, file_5)

    def test_bond(self):

        logging.info('*** bond ***')

        bot = ShellBot(fan='f')
        bot.space = mock.Mock()
        bot.store = mock.Mock()
        bot.dispatch = mock.Mock()

        bot.bond(reset=True)
        self.assertTrue(bot.space.delete_space.called)
        self.assertTrue(bot.space.bond.called)
        self.assertTrue(bot.store.bond.called)
        self.assertTrue(bot.dispatch.called)

    def test_add_moderators(self):

        logging.info('*** add_moderators ***')

        with mock.patch.object(my_bot.space,
                               'add_moderators',
                               return_value=None) as mocked:
            my_bot.add_moderators(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_add_participants(self):

        logging.info('*** add_participants ***')

        with mock.patch.object(my_bot.space,
                               'add_participants',
                               return_value=None) as mocked:
            my_bot.add_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_remove_participants(self):

        logging.info('*** remove_participants ***')

        with mock.patch.object(my_bot.space,
                               'remove_participants',
                               return_value=None) as mocked:
            my_bot.remove_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_dispose(self):

        logging.info('*** dispose ***')

        with mock.patch.object(my_bot.space,
                               'dispose',
                               return_value=None) as mocked:

            my_bot.dispose(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

        my_context.clear()
        with mock.patch.object(my_bot.space,
                               'delete_space',
                               return_value=None) as mocked:

            my_bot.dispose()
            mocked.assert_called_with(title='Collaboration space')

    def test_hook(self):

        logging.info('*** hook ***')

        my_context.set('server.url', 'http://here.you.go:123')
        server = mock.Mock()
        with mock.patch.object(my_bot.space,
                               'register',
                               return_value=None) as mocked:

            my_bot.hook(server=server)
            self.assertFalse(mocked.called)

            my_context.set('server.binding', '0.0.0.0')
            my_bot.hook(server=server)
            mocked.assert_called_with(hook_url='http://here.you.go:123/hook')

    def test_get_hook(self):

        logging.info('*** get_hook ***')

        my_context.set('server.url', 'http://here.you.go:123')
        self.assertEqual(my_bot.get_hook(), my_bot.space.webhook)

    def test_run(self):

        logging.info('*** run ***')

        bot = ShellBot(context=my_context, fan='f')
        bot.space=LocalSpace(bot=bot)

        bot.start = mock.Mock()
        bot.space.run = mock.Mock()

        bot.run()
        self.assertTrue(bot.start.called)
        self.assertTrue(bot.space.run.called)

        class MyServer(object):
            def __init__(self, bot):
                self.bot = bot

            def add_route(self, route, **kwargs):
                pass

            def run(self):
                self.bot.set("has_been_ran", True)

        server = MyServer(bot=bot)
        bot.run(server=server)
        self.assertTrue(bot.get("has_been_ran"))

    def test_start(self):

        logging.info('*** start ***')

        bot = ShellBot(context=my_context, fan='f')
        bot.space=LocalSpace(bot=bot)

        bot.start_processes = mock.Mock()
        bot.say = mock.Mock()
        bot.on_start = mock.Mock()

        bot.start()
        self.assertTrue(bot.ears is not None)
        self.assertTrue(bot.inbox is not None)
        self.assertTrue(bot.mouth is not None)
        self.assertTrue(bot.start_processes.called)
        self.assertTrue(bot.say.called)
        self.assertTrue(bot.on_start.called)

    def test_static(self):

        logging.info('*** static test ***')

        my_bot.start()
        time.sleep(0.1)
        my_bot.stop()

        self.assertEqual(my_bot.context.get('listener.counter', 0), 0)
        self.assertEqual(my_bot.context.get('worker.counter', 0), 0)
        self.assertEqual(my_bot.context.get('speaker.counter', 0), 0)

    def test_say(self):

        logging.info('*** say ***')

        bot = ShellBot(context=my_context, fan='f')

        bot.say('')
        bot.say(None)

        with mock.patch.object(bot.speaker,
                               'process',
                               return_value=None) as mocked:

            bot.say('test')
            bot.say('test', content='test')
            bot.say('test', file='test.yaml')

        bot.mouth = Queue()
        bot.mouth.put = mock.Mock()
        bot.speaker.process = mock.Mock()

        bot.say('test')
        bot.say('test', content='test')
        bot.say('test', file='test.yaml')

        self.assertTrue(bot.mouth.put.called)
        self.assertFalse(bot.speaker.process.called)

        bot.mouth = Queue()

        message_0 = None
        bot.say(message_0)
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        message_0 = ''
        bot.say(message_0)
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        message_1 = 'hello'
        bot.say(message_1)
        self.assertEqual(bot.mouth.get().text, message_1)

        message_2 = 'world'
        bot.say(message_2)
        self.assertEqual(bot.mouth.get().text, message_2)

        message_3 = 'hello'
        content_3 = 'world'
        bot.say(message_3, content=content_3)
        item = bot.mouth.get()
        self.assertEqual(item.text, message_3)
        self.assertEqual(item.content, content_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        bot.say(message_4, file=file_4)
        item = bot.mouth.get()
        self.assertEqual(item.text, message_4)
        self.assertEqual(item.content, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        content_5 = 'world'
        file_5 = 'http://some.server/some/file'
        bot.say(message_5, content=content_5, file=file_5)
        item = bot.mouth.get()
        self.assertEqual(item.text, message_5)
        self.assertEqual(item.content, content_5)
        self.assertEqual(item.file, file_5)

    def test_remember(self):

        logging.info('***** remember')

        self.assertEqual(my_bot.recall('sca.lar'), None)
        my_bot.remember('sca.lar', 'test')
        self.assertEqual(my_bot.recall('sca.lar'), 'test')

        self.assertEqual(my_bot.recall('list'), None)
        my_bot.remember('list', ['hello', 'world'])
        self.assertEqual(my_bot.recall('list'), ['hello', 'world'])

        self.assertEqual(my_bot.recall('dict'), None)
        my_bot.remember('dict', {'hello': 'world'})
        self.assertEqual(my_bot.recall('dict'), {'hello': 'world'})

    def test_recall(self):

        logging.info('***** recall')

        # undefined key
        self.assertEqual(my_bot.recall('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(my_bot.recall('hello', whatever), whatever)

        # set the key
        my_bot.remember('hello', 'world')
        self.assertEqual(my_bot.recall('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(my_bot.recall('hello', 'whatever'), 'world')

        # except when set to None
        my_bot.remember('special', None)
        self.assertEqual(my_bot.recall('special', []), [])

    def test_forget(self):

        logging.info('***** forget')

        # set the key and then forget it
        my_bot.remember('hello', 'world')
        self.assertEqual(my_bot.recall('hello'), 'world')
        my_bot.forget('hello')
        self.assertEqual(my_bot.recall('hello'), None)

        # set multiple keys and then forget all of them
        my_bot.remember('hello', 'world')
        my_bot.remember('bunny', "What'up, Doc?")
        self.assertEqual(my_bot.recall('hello'), 'world')
        self.assertEqual(my_bot.recall('bunny'), "What'up, Doc?")
        my_bot.forget()
        self.assertEqual(my_bot.recall('hello'), None)
        self.assertEqual(my_bot.recall('bunny'), None)

    def test_append(self):

        logging.info('***** append')

        my_bot.append('famous', 'hello, world')
        my_bot.append('famous', "What'up, Doc?")
        self.assertEqual(my_bot.recall('famous'),
                         ['hello, world', "What'up, Doc?"])

    def test_update(self):

        logging.info('***** update')

        my_bot.update('input', 'PO#', '1234A')
        my_bot.update('input', 'description', 'part does not fit')
        self.assertEqual(my_bot.recall('input'),
                         {u'PO#': u'1234A', u'description': u'part does not fit'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
