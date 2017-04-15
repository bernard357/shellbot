#!/usr/bin/env python

import colorlog
import unittest
import logging
from mock import MagicMock
import os
import mock
from multiprocessing import Process, Queue
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.bot import ShellBot
from shellbot.space import SparkSpace


class BotTests(unittest.TestCase):

    def test_init(self):

        logging.info('*** Init test ***')

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

    def test_configuration(self):

        logging.info('*** Configuration test ***')

        bot = ShellBot()

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

        settings = {
            'bot': {'name': 'testy'},
            'spark': {
                'room': 'space name',
                'moderators': 'foo.bar@acme.com',
                'webhook': 'http://to.no.where/',
            },
        }
        bot.configure_from_dict(settings)
        self.assertEqual(bot.context.get('bot.name'), 'testy')
        self.assertEqual(bot.context.get('spark.room'), 'space name')
        self.assertEqual(bot.context.get('spark.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(bot.context.get('spark.webhook'), 'http://to.no.where/')

        bot.configure_from_path('test_settings/regular.yaml')
        self.assertTrue(bot.context is not None)
        self.assertTrue(bot.space is not None)
        self.assertTrue(bot.store is None)
        self.assertTrue(bot.mouth is not None)
        self.assertTrue(bot.inbox is not None)
        self.assertTrue(bot.ears is not None)
        self.assertTrue(bot.shell is not None)
        self.assertTrue(bot.speaker is not None)
        self.assertTrue(bot.worker is not None)
        self.assertTrue(bot.listener is not None)

    def test_static(self):

        logging.info('*** Static test ***')

        bot = ShellBot()

        settings = {
            'bot': {'name': 'shelly'},
            'spark': {
                'room': '*Test Space',
                'moderators': 'foo.bar@acme.com',
            },
        }

        bot.configure_from_dict(settings)

        bot.start()
        time.sleep(1.0)
        bot.stop()

        self.assertEqual(bot.context.get('listener.counter', 0), 0)
        self.assertEqual(bot.context.get('worker.counter', 0), 0)
        self.assertEqual(bot.context.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        bot = ShellBot()

        settings = {
            'bot': {'name': 'shelly'},
            'spark': {
                'room': '*Test Space',
                'moderators': 'foo.bar@acme.com',
            },
        }

        bot.configure_from_dict(settings)

        with mock.patch.object(bot.space,
                               'post_message',
                               return_value=None) as mocked:

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

            self.assertEqual(bot.context.get('listener.counter', 0), 6)
            self.assertEqual(bot.context.get('worker.counter', 0), 1)
            self.assertTrue(bot.context.get('speaker.counter', 0) == 5)

    def test_connect(self):

        logging.info('*** Connect test ***')

        settings = {
            'bot': {'name': 'shelly'},
            'spark': {
                'room': '*Test Space',
                'moderators': 'foo.bar@acme.com',
            },
        }

        bot = ShellBot()
        bot.configure_from_dict(settings)

        bot.start()
        bot.shell.say('hello world')

        time.sleep(5.0)
        bot.stop()

if __name__ == '__main__':

    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(asctime)-2s %(log_color)s%(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)

    logging.getLogger('').handlers = []
    logging.getLogger('').addHandler(handler)

    logging.getLogger('').setLevel(level=logging.DEBUG)

    sys.exit(unittest.main())
