#!/usr/bin/env python

import unittest
import logging
from mock import MagicMock
import os
from multiprocessing import Process, Queue
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.bot import ShellBot


class BotTests(unittest.TestCase):

    def test_init(self):

        print('*** Init test ***')

        context = Context()

        bot = ShellBot(context=context)

        self.assertEqual(bot.context, context)
        self.assertTrue(bot.store is None)
        self.assertTrue(bot.mouth is not None)
        self.assertTrue(bot.inbox is not None)
        self.assertTrue(bot.ears is not None)
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.sender is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

        bot = ShellBot(context=context,
                       mouth='m',
                       inbox='i',
                       ears='e',
                       store='s')

        self.assertEqual(bot.context, context)
        self.assertEqual(bot.store, 's')
        self.assertEqual(bot.mouth, 'm')
        self.assertEqual(bot.inbox, 'i')
        self.assertEqual(bot.ears, 'e')
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.sender is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

    def test_configuration(self):

        print('*** Configuration test ***')

        context = Context()

        bot = ShellBot(context=context)

        with self.assertRaises(KeyError):
            bot.configure_from_dict({})

        with self.assertRaises(KeyError):
            settings = {'missing': 'bot' }
            bot.configure_from_dict(settings)

        with self.assertRaises(KeyError):
            settings = { 'bot': {'missing': 'name'} }
            bot.configure_from_dict(settings)

        with self.assertRaises(KeyError):
            settings = {
                'bot': {'name': 'testy'},
                'missing': 'spark',
            }
            bot.configure_from_dict(settings)

        with self.assertRaises(KeyError):
            settings = {
                'bot': {'name': 'testy'},
                'spark': {'missing': 'space'},
            }
            bot.configure_from_dict(settings)

        with self.assertRaises(KeyError):
            settings = {
                'bot': {'name': 'testy'},
                'spark': {
                    'space': 'space name',
                    'missing': 'moderators',
                },
            }
            bot.configure_from_dict(settings)

        with self.assertRaises(KeyError):
            settings = {
                'bot': {'name': 'testy'},
                'spark': {
                    'space': 'space name',
                    'moderators': 'space name',
                },
                'missing': 'server',
            }
            bot.configure_from_dict(settings)

        with self.assertRaises(KeyError):
            settings = {
                'bot': {'name': 'testy'},
                'spark': {
                    'space': 'space name',
                    'moderators': 'space name',
                },
                'server': {'missing': 'url'},
            }
            bot.configure_from_dict(settings)

        settings = {
            'bot': {'name': 'testy'},
            'spark': {
                'space': 'space name',
                'moderators': 'foo.bar@acme.com',
            },
            'server': {'url': 'http://to.no.where/'},
        }
        bot.configure_from_dict(settings)
        self.assertEqual(bot.context.get('bot.name'), 'testy')
        self.assertEqual(bot.context.get('spark.space'), 'space name')
        self.assertEqual(bot.context.get('spark.moderators'),
                         'foo.bar@acme.com')
        self.assertEqual(bot.context.get('server.url'), 'http://to.no.where/')

        bot.configure_from_path('test_settings/regular.yaml')
        self.assertEqual(bot.context, context)
        self.assertTrue(bot.store is None)
        self.assertTrue(bot.mouth is not None)
        self.assertTrue(bot.inbox is not None)
        self.assertTrue(bot.ears is not None)
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.sender is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

    def test_static(self):

        print('*** Static test ***')

        context = Context()
        bot = ShellBot(context=context,
                       mouth=None,
                       inbox=None,
                       ears=None,
                       store=None)

        bot.start()

        time.sleep(1.0)
        bot.stop()

        self.assertEqual(context.get('listener.counter', 0), 0)
        self.assertEqual(context.get('worker.counter', 0), 0)
        self.assertEqual(context.get('sender.counter', 0), 0)

    def test_dynamic(self):

        print('*** Dynamic test ***')

        context = Context()
        bot = ShellBot(context=context,
                       mouth=None,
                       inbox=None,
                       ears=None,
                       store=None)
        bot.start()

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

        time.sleep(5.0)
        bot.stop()

        self.assertEqual(context.get('listener.counter', 0), 6)
        self.assertEqual(context.get('worker.counter', 0), 1)
        self.assertTrue(context.get('sender.counter', 0) > 0)


if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
