#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import os
import mock
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, SparkSpace


class BotTests(unittest.TestCase):

    def test_init(self):

        logging.info('*** init***')

        context = Context()

        bot = ShellBot(context=context)

        self.assertEqual(bot.context, context)
        self.assertTrue(bot.space is not None)
        self.assertTrue(bot.store is None)
        self.assertTrue(bot.mouth is not None)
        self.assertTrue(bot.inbox is not None)
        self.assertTrue(bot.ears is not None)
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.speaker is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

        space = SparkSpace(context=context)
        bot = ShellBot(context=context,
                       space=space,
                       mouth='m',
                       inbox='i',
                       ears='e',
                       store='s')

        self.assertEqual(bot.context, context)
        self.assertEqual(bot.space, space)
        self.assertEqual(bot.store, 's')
        self.assertEqual(bot.mouth, 'm')
        self.assertEqual(bot.inbox, 'i')
        self.assertEqual(bot.ears, 'e')
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

        bot = ShellBot()

        with self.assertRaises(KeyError):
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

        bot = ShellBot()
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
                'moderators': 'foo.bar@acme.com',
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
        bot = ShellBot(context=context, check=True)
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

    def test_load_commands(self):

        logging.info('*** load_commands ***')

        bot = ShellBot()
        with mock.patch.object(bot.shell,
                               'load_commands',
                               return_value=None) as mocked:
            bot.load_commands(['a', 'b', 'c', 'd'])
            mocked.called

    def test_say(self):

        logging.info('*** say ***')

        bot = ShellBot()

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
        markdown_3 = 'world'
        bot.say(message_3, markdown=markdown_3)
        item = bot.mouth.get()
        self.assertEqual(item.message, message_3)
        self.assertEqual(item.markdown, message_3+'\n\n'+markdown_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        bot.say(message_4, file=file_4)
        item = bot.mouth.get()
        self.assertEqual(item.message, message_4)
        self.assertEqual(item.markdown, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        markdown_5 = 'world'
        file_5 = 'http://some.server/some/file'
        bot.say(message_5, markdown=markdown_5, file=file_5)
        item = bot.mouth.get()
        self.assertEqual(item.message, message_5)
        self.assertEqual(item.markdown, message_5+'\n\n'+markdown_5)
        self.assertEqual(item.file, file_5)

    def test_add_moderators(self):

        logging.info('*** add_moderators ***')

        bot = ShellBot()
        with mock.patch.object(bot.space,
                               'add_moderators',
                               return_value=None) as mocked:
            bot.add_moderators(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_add_participants(self):

        logging.info('*** add_participants ***')

        bot = ShellBot()
        with mock.patch.object(bot.space,
                               'add_participants',
                               return_value=None) as mocked:
            bot.add_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_dispose(self):

        logging.info('*** dispose ***')

        bot = ShellBot()
        with mock.patch.object(bot.space,
                               'dispose',
                               return_value=None) as mocked:
            bot.dispose(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_static(self):

        logging.info('*** static test ***')

        bot = ShellBot()

        settings = {
            'bot': {'name': 'shelly'},
            'spark': {
                'room': '*Test Space',
                'moderators': 'foo.bar@acme.com',
            },
        }

        bot.configure(settings)

#        bot.start()
#        time.sleep(1.0)
#        bot.stop()

        self.assertEqual(bot.context.get('listener.counter', 0), 0)
        self.assertEqual(bot.context.get('worker.counter', 0), 0)
        self.assertEqual(bot.context.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** dynamic test ***')

        bot = ShellBot()

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

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
