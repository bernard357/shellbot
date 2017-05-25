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
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** init***')

        context = Context()

        bot = ShellBot(context=context)

        self.assertEqual(bot.context, context)
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

        bot = ShellBot(context=context,
                       type='local',
                       mouth='m',
                       inbox='i',
                       ears='e',
                       fan='f',
                       store='s')

        self.assertEqual(bot.context, context)
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

        space = SparkSpace(bot=bot)
        bot = ShellBot(context=context,
                       space=space,
                       mouth='m',
                       inbox='i',
                       ears='e',
                       fan='f',
                       store='s')

        self.assertEqual(bot.context, context)
        self.assertEqual(bot.space, space)
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

    def test_configuration(self):

        logging.info('*** configure ***')

        context = Context()
        bot = ShellBot(context=context, fan='f')
        bot.space=LocalSpace(bot=bot)
        bot.configure({})

        bot = ShellBot()
        settings = {

            'bot': {
                'on_start': 'Start!',
                'on_stop': 'Stop!',
            },

            'spark': {
                'room': 'space name',
                'moderators': 'foo.bar@acme.com',
                'participants': ['joe.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.no.where',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }
        bot.configure(settings)
        self.assertEqual(bot.context.get('bot.on_start'), 'Start!')
        self.assertEqual(bot.context.get('bot.on_stop'), 'Stop!')
        self.assertEqual(bot.context.get('spark.room'), 'space name')
        self.assertEqual(bot.context.get('spark.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.context.get('spark.participants'),
                         ['joe.bar@acme.com'])
        self.assertEqual(bot.context.get('server.url'), 'http://to.no.where')
        self.assertEqual(bot.context.get('server.hook'), '/hook')

        bot = ShellBot(fan='f')
        bot.configure_from_path(os.path.dirname(os.path.abspath(__file__))
                                + '/test_settings/regular.yaml')
        self.assertEqual(bot.context.get('bot.on_start'),
                         'How can I help you?')
        self.assertEqual(bot.context.get('bot.on_stop'), 'Bye for now')
        self.assertEqual(bot.context.get('spark.room'), 'Support room')
        self.assertEqual(bot.context.get('spark.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.context.get('spark.participants'),
                         ['joe.bar@acme.com', 'super.support@help.org'])
        self.assertEqual(bot.context.get('server.url'),
                         'http://73a1e282.ngrok.io')
        self.assertEqual(bot.context.get('server.hook'), '/hook')

    def test_configuration_2(self):

        logging.info('*** configure 2 ***')

        settings = {

            'bot': {
                'on_start': 'Start!',
                'on_stop': 'Stop!',
            },

            'spark': {
                'room': 'Support room',
                'moderators': 'foo.bar@acme.com',  # to be turned to list
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
        self.assertEqual(bot.context.get('spark.room'), 'Support room')
        self.assertEqual(bot.context.get('spark.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.context.get('spark.participants'), [])
        self.assertEqual(bot.context.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(bot.context.get('server.hook'), '/hook')
        self.assertEqual(bot.context.get('server.trigger'), '/trigger')
        self.assertEqual(bot.context.get('server.binding'), '0.0.0.0')
        self.assertEqual(bot.context.get('server.port'), 8080)

    def test_configure_default(self):

        logging.info('*** configure/default configuration ***')

        os.environ["BOT_ON_START"] = 'Start!'
        os.environ["BOT_ON_STOP"] = 'Stop!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CHAT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'

        bot = ShellBot(fan='f')
        bot.configure()

        self.assertEqual(bot.context.get('bot.on_start'), 'Start!')
        self.assertEqual(bot.context.get('bot.on_stop'), 'Stop!')
        self.assertEqual(bot.context.get('spark.room'), 'Support room')
        self.assertEqual(bot.context.get('spark.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.context.get('spark.participants'), [])

        self.assertEqual(bot.context.get('spark.token'), '*token')

        self.assertEqual(bot.context.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(bot.context.get('server.hook'), '/hook')
        self.assertEqual(bot.context.get('server.binding'), '0.0.0.0')
        self.assertEqual(bot.context.get('server.port'), 8080)

        os.environ['CHAT_ROOM_TITLE'] = 'Notifications'
        bot = ShellBot(settings=None, configure=True, fan='f')

    def test_get(self):

        logging.info('*** get ***')

        os.environ["BOT_ON_START"] = 'Start!'
        os.environ["BOT_ON_STOP"] = 'Stop!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CHAT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'

        bot = ShellBot(fan='f')
        bot.configure()

        self.assertEqual(bot.get('bot.on_start'), 'Start!')
        self.assertEqual(bot.get('bot.on_stop'), 'Stop!')
        self.assertEqual(bot.get('spark.room'), 'Support room')
        self.assertEqual(bot.get('spark.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.get('spark.participants'), [])

        self.assertEqual(bot.get('spark.token'), '*token')

        self.assertEqual(bot.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(bot.get('server.hook'), '/hook')
        self.assertEqual(bot.get('server.binding'), '0.0.0.0')
        self.assertEqual(bot.get('server.port'), 8080)

        os.environ['CHAT_ROOM_TITLE'] = 'Notifications'
        bot = ShellBot(settings=None, configure=True, fan='f')
        self.assertEqual(bot.get('spark.room'), 'Notifications')

    def test_register(self):

        logging.info('*** register ***')

        bot = ShellBot(fan='f')

        with self.assertRaises(AssertionError):
            bot.register('*unknown*event', lambda : 'ok')
        with self.assertRaises(AttributeError):
            bot.register('bond', lambda : 'ok')
        with self.assertRaises(AttributeError):
            bot.register('dispose', lambda : 'ok')

        counter = MyCounter('counter #1')
        bot.register('bond', counter)
        bot.register('dispose', counter)
        with self.assertRaises(AttributeError):
            bot.register('start', counter)
        with self.assertRaises(AttributeError):
            bot.register('stop', counter)
        with self.assertRaises(AssertionError):
            bot.register('*unknown*event', counter)

        bot.register('bond', MyCounter('counter #2'))

        self.assertEqual(len(bot.registered['bond']), 2)
        self.assertEqual(len(bot.registered['dispose']), 1)
        self.assertEqual(len(bot.registered['start']), 0)
        self.assertEqual(len(bot.registered['stop']), 0)

    def test_dispatch(self):

        logging.info('*** dispatch ***')

        bot = ShellBot(fan='f')

        counter = MyCounter('counter #1')
        bot.register('bond', counter)
        bot.register('dispose', counter)

        bot.register('bond', MyCounter('counter #2'))
        bot.register('dispose', MyCounter('counter #3'))

        bot.dispatch('bond')
        bot.dispatch('dispose')

        with self.assertRaises(AssertionError):
            bot.dispatch('*unknown*event')

        self.assertEqual(counter.count, 2)

    def test_load_commands(self):

        logging.info('*** load_commands ***')

        bot = ShellBot(fan='f')
        with mock.patch.object(bot.shell,
                               'load_commands',
                               return_value=None) as mocked:
            bot.load_commands(['a', 'b', 'c', 'd'])
            mocked.called

    def test_say(self):

        logging.info('*** say ***')

        bot = ShellBot(mouth=Queue(), fan='f')

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
        self.assertEqual(bot.mouth.get(), message_1)

        message_2 = 'world'
        bot.say(message_2)
        self.assertEqual(bot.mouth.get(), message_2)

        message_3 = 'hello'
        content_3 = 'world'
        bot.say(message_3, content=content_3)
        item = bot.mouth.get()
        self.assertEqual(item.message, message_3)
        self.assertEqual(item.content, content_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        bot.say(message_4, file=file_4)
        item = bot.mouth.get()
        self.assertEqual(item.message, message_4)
        self.assertEqual(item.content, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        content_5 = 'world'
        file_5 = 'http://some.server/some/file'
        bot.say(message_5, content=content_5, file=file_5)
        item = bot.mouth.get()
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

        context = Context()
        bot = ShellBot(context=context, fan='f')
        bot.space=LocalSpace(bot=bot)
        with mock.patch.object(bot.space,
                               'add_moderators',
                               return_value=None) as mocked:
            bot.add_moderators(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_add_participants(self):

        logging.info('*** add_participants ***')

        context = Context()
        bot = ShellBot(context=context, fan='f')
        bot.space=LocalSpace(bot=bot)
        with mock.patch.object(bot.space,
                               'add_participants',
                               return_value=None) as mocked:
            bot.add_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_dispose(self):

        logging.info('*** dispose ***')

        context = Context()
        bot = ShellBot(context=context, fan='f')
        bot.space=LocalSpace(bot=bot)

        with mock.patch.object(bot.space,
                               'dispose',
                               return_value=None) as mocked:

            bot.dispose(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

        spark_settings = {

            'bot': {
                'on_start': 'Welcome to this on-demand collaborative room',
                'on_stop': 'Bot is now quitting the room, bye',
            },

            'spark': {
                'room': 'On-demand collaboration',
                'moderators': 'bernard.paques@dimensiondata.com',
                'token': '<bot token here>',
            },

            'server': {
                'url': 'http://why.are.here:890',
                'trigger': '/trigger',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        bot.space = None
        bot.configure(spark_settings)

        with mock.patch.object(bot.space,
                               'delete_space',
                               return_value=None) as mocked:

            bot.dispose()
            mocked.assert_called_with(title='On-demand collaboration')

    def test_hook(self):

        logging.info('*** hook ***')

        context = Context()
        context.set('server.url', 'http://here.you.go:123')
        bot = ShellBot(context=context, fan='f')
        bot.space=LocalSpace(bot=bot)
        server = mock.Mock()
        with mock.patch.object(bot.space,
                               'register',
                               return_value=None) as mocked:

            bot.hook(server=server)
            self.assertFalse(mocked.called)

            context.set('server.binding', '0.0.0.0')
            bot.hook(server=server)
            mocked.assert_called_with(hook_url='http://here.you.go:123/hook')

    def test_get_hook(self):

        logging.info('*** get_hook ***')

        context = Context()
        context.set('server.url', 'http://here.you.go:123')
        bot = ShellBot(context=context, fan='f')
        bot.space=LocalSpace(bot=bot)
        self.assertEqual(bot.get_hook(), bot.space.webhook)

    def test_run(self):

        logging.info('*** run ***')

        bot = ShellBot(fan='f')
        bot.space=LocalSpace(bot=bot)

        bot.start = mock.Mock()
        bot.space.work = mock.Mock()

        bot.run()
        self.assertTrue(bot.start.called)
        self.assertTrue(bot.space.work.called)

        server = mock.Mock()
        bot.run(server=server)
        self.assertTrue(server.run.called)

    def test_start(self):

        logging.info('*** start ***')

        bot = ShellBot(fan='f')
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

        bot = ShellBot(ears=Queue(),
                       inbox=Queue(),
                       mouth=Queue(),
                       fan='f')

        settings = {
            'bot': {'name': 'shelly'},
            'spark': {
                'room': '*Test Space',
                'moderators': 'foo.bar@acme.com',
            },
        }

        bot.configure(settings)

        bot.start()
        time.sleep(0.1)
        bot.stop()

        self.assertEqual(bot.context.get('listener.counter', 0), 0)
        self.assertEqual(bot.context.get('worker.counter', 0), 0)
        self.assertEqual(bot.context.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** dynamic test ***')

        bot = ShellBot(ears=Queue(), fan='f')

        settings = {
            'bot': {'name': 'shelly'},
            'spark': {
                'room': '*Test Space',
                'moderators': 'foo.bar@acme.com',
            },
        }

        bot.configure(settings)

        with mock.patch.object(bot.space,
                               'post_message',
                               return_value=None) as mocked:

#            bot.start()

            bot.ears.put('hello world')

            bot.ears.put({
                  "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
                  "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
                  "roomType" : "group",
                  "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
                  "toPersonEmail" : "julie@example.com",
                  "text" : "PROJECT UPDATE - A new project plan has been published on Box: http://box.com/s/lf5vj. The PM for this project is Mike C. and the Engineering Manager is Jane W.",
                  "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
                  "files" : [ "http://www.example.com/images/media.png" ],
                  "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
                  "personEmail" : "matt@example.com",
                  "created" : "2015-10-18T14:26:16+00:00",
                  "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
                })

            bot.ears.put({
                  "id" : "2_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
                  "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
                  "roomType" : "group",
                  "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
                  "toPersonEmail" : "julie@example.com",
                  "text" : "/shelly version",
                  "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
                  "personEmail" : "matt@example.com",
                  "created" : "2015-10-18T14:26:16+00:00",
                  "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
                })

            bot.ears.put({
                  "id" : "3_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
                  "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
                  "roomType" : "group",
                  "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
                  "toPersonEmail" : "julie@example.com",
                  "text" : "/shelly help",
                  "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
                  "personEmail" : "matt@example.com",
                  "created" : "2015-10-18T14:26:16+00:00",
                  "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
                })

            bot.ears.put({
                  "id" : "3_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
                  "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
                  "roomType" : "group",
                  "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
                  "toPersonEmail" : "julie@example.com",
                  "text" : "/shelly sleep 1",
                  "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
                  "personEmail" : "matt@example.com",
                  "created" : "2015-10-18T14:26:16+00:00",
                  "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
                })

            bot.ears.put({
                  "id" : "4_2lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
                  "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
                  "roomType" : "group",
                  "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
                  "toPersonEmail" : "julie@example.com",
                  "text" : "PROJECT UPDATE - A new project plan has been published on Box: http://box.com/s/lf5vj. The PM for this project is Mike C. and the Engineering Manager is Jane W.",
                  "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
                  "files" : [ "http://www.example.com/images/media.png" ],
                  "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
                  "personEmail" : "matt@example.com",
                  "created" : "2015-10-18T14:26:16+00:00",
                  "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ]
                })

#            time.sleep(5.0)
#            bot.stop()
#
#            self.assertEqual(bot.context.get('listener.counter', 0), 6)
#            self.assertEqual(bot.context.get('worker.counter', 0), 1)
#            self.assertTrue(bot.context.get('speaker.counter', 0) == 5)

#    def test_connect(self):
#
#        logging.info('*** Connect test ***')
#
#        settings = {
#            'bot': {'name': 'shelly'},
#            'spark': {
#                'room': '*Test Space',
#                'moderators': 'foo.bar@acme.com',
#            },
#        }
#
#        bot = ShellBot()
#        bot.configure(settings)
#
#        bot.start()
#        bot.shell.say('hello world')
#
#        time.sleep(5.0)
#        bot.stop()

    def test_say(self):

        logging.info('*** say ***')

        context = Context()

        bot = ShellBot(context=context, fan='f')

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

        store = MemoryStore()
        bot = ShellBot(store=store)

        self.assertEqual(bot.recall('sca.lar'), None)
        bot.remember('sca.lar', 'test')
        self.assertEqual(bot.recall('sca.lar'), 'test')

        self.assertEqual(bot.recall('list'), None)
        bot.remember('list', ['hello', 'world'])
        self.assertEqual(bot.recall('list'), ['hello', 'world'])

        self.assertEqual(bot.recall('dict'), None)
        bot.remember('dict', {'hello': 'world'})
        self.assertEqual(bot.recall('dict'), {'hello': 'world'})

    def test_recall(self):

        logging.info('***** recall')

        store = MemoryStore()
        bot = ShellBot(store=store)

        # undefined key
        self.assertEqual(bot.recall('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(bot.recall('hello', whatever), whatever)

        # set the key
        bot.remember('hello', 'world')
        self.assertEqual(bot.recall('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(bot.recall('hello', 'whatever'), 'world')

        # except when set to None
        bot.remember('special', None)
        self.assertEqual(bot.recall('special', []), [])

    def test_forget(self):

        logging.info('***** forget')

        store = MemoryStore()
        bot = ShellBot(store=store)

        # set the key and then forget it
        bot.remember('hello', 'world')
        self.assertEqual(bot.recall('hello'), 'world')
        bot.forget('hello')
        self.assertEqual(bot.recall('hello'), None)

        # set multiple keys and then forget all of them
        bot.remember('hello', 'world')
        bot.remember('bunny', "What'up, Doc?")
        self.assertEqual(bot.recall('hello'), 'world')
        self.assertEqual(bot.recall('bunny'), "What'up, Doc?")
        bot.forget()
        self.assertEqual(bot.recall('hello'), None)
        self.assertEqual(bot.recall('bunny'), None)

    def test_append(self):

        logging.info('***** append')

        store = MemoryStore()
        bot = ShellBot(store=store)

        bot.append('famous', 'hello, world')
        bot.append('famous', "What'up, Doc?")
        self.assertEqual(bot.recall('famous'),
                         ['hello, world', "What'up, Doc?"])

    def test_update(self):

        logging.info('***** update')

        store = MemoryStore()
        bot = ShellBot(store=store)

        bot.update('input', 'PO#', '1234A')
        bot.update('input', 'description', 'part does not fit')
        self.assertEqual(bot.recall('input'),
                         {u'PO#': u'1234A', u'description': u'part does not fit'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
