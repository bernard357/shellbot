#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import request
import unittest
import json
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
import yaml

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot
from shellbot.events import Event, Message, Attachment, Join, Leave
from shellbot.spaces import Space, SparkSpace


# unit tests
cisco_spark_bearer = None

# functional tests
# cisco_spark_bearer = os.environ.get('CISCO_SPARK_BOT_TOKEN')


class Fake(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeRoom(Fake):
    id = '*id'
    title = '*title'
    teamId = None


class FakeMessage(Fake):
    id = '*id'
    message = '*message'
    _json = {'text': '*message'}


class FakePerson(Fake):
    id = 'Y2lzY29zcGFyazovL3VzL1RFQU0Yy0xMWU2LWE5ZDgtMjExYTBkYzc5NzY5'
    personEmail = 'a@me.com'
    displayName = 'dusty (bot)'


class FakeApi(object):

    def __init__(self, rooms=[], teams=[], messages=[], new_room=None):

        new_room = new_room if new_room else FakeRoom()

        self.rooms = Fake()
        self.rooms.list = mock.Mock(return_value=rooms)
        self.rooms.create = mock.Mock(return_value=new_room)
        self.rooms.delete = mock.Mock()

        self.teams = Fake()
        self.teams.list = mock.Mock(return_value=teams)
        self.teams.create = mock.Mock()

        self.memberships = Fake()
        self.memberships.create = mock.Mock()

        self.messages = Fake()
        self.messages.list = mock.Mock(return_value=messages)
        self.messages.create = mock.Mock(return_value=FakeMessage())
        self.messages.delete = mock.Mock()
        self.messages.get = mock.Mock(return_value=FakeMessage())

        self.webhooks = Fake()
        self.webhooks.create = mock.Mock()

        self.people = Fake()
        self.people.me = mock.Mock(return_value=FakePerson())


my_bot = ShellBot()

my_queue = Queue()

my_message = {
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "created" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
}

my_join = {
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "created" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
}

my_leave = {
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvOTJkYjNiZTAtNDNiZC0xMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "roomId" : "Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0",
    "roomType" : "group",
    "toPersonId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mMDZkNzFhNS0wODMzLTRmYTUtYTcyYS1jYzg5YjI1ZWVlMmX",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "personEmail" : "matt@example.com",
    "created" : "2015-10-18T14:26:16+00:00",
    "mentionedPeople" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
    "from_id" : "Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY",
    "mentioned_ids" : [ "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM", "Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg" ],
}


class SparkSpaceTests(unittest.TestCase):

    def test_init(self):

        logging.info("*** init")

        space = SparkSpace(bot=my_bot, token='b')
        self.assertEqual(space.token, 'b')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, space.DEFAULT_SPACE_TITLE)
        self.assertEqual(space.teamId, None)

        space = SparkSpace(bot=my_bot, token='b', personal_token='c')
        self.assertEqual(space.token, 'b')
        self.assertEqual(space.personal_token, 'c')

    def test_is_ready(self):

        logging.info("*** is_ready")

        my_bot.context = Context()
        space = SparkSpace(bot=my_bot)
        self.assertFalse(space.is_ready)

        context = Context(settings={'space.id': '123'})
        bot = ShellBot(context=context)
        space = Space(bot=bot)
        self.assertTrue(space.is_ready)

        space = Space(bot=my_bot)
        space.id = '*id'
        self.assertTrue(space.is_ready)

    def test_configure(self):

        logging.info("*** configure")

        my_bot.context = Context()
        space = SparkSpace(bot=my_bot)
        space.configure(settings={  # from settings to member attributes
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
                'personal_token': '*personal*secret*token',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })
        self.assertEqual(space.token, 'hkNWEtMJNkODVGlZWU1NmYtyY')
        self.assertEqual(space.personal_token, '*personal*secret*token')
        self.assertEqual(space.id, None)   #  set after bond()
        self.assertEqual(space.title, space.DEFAULT_SPACE_TITLE)
        self.assertEqual(space.teamId, None)

        my_bot.context=Context()
        space = SparkSpace(bot=my_bot)
        space.configure({
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        self.assertEqual(space.configured_title(), 'My preferred room')

        self.assertEqual(space.bot.context.get('spark.room'), 'My preferred room')
        self.assertEqual(space.bot.context.get('spark.moderators'),
            ['foo.bar@acme.com', 'joe.bar@corporation.com'])
        self.assertEqual(space.bot.context.get('spark.participants'),
            ['alan.droit@azerty.org', 'bob.nard@support.tv'])
        self.assertEqual(space.bot.context.get('spark.team'), 'Anchor team')

        my_bot.context=Context()
        space = SparkSpace(bot=my_bot)
        space.configure({
            'spark': {
                'room': 'My preferred room',
                'moderators': 'foo.bar@acme.com',
                'participants': 'alan.droit@azerty.org',
            }
        })
        self.assertEqual(space.bot.context.get('spark.room'), 'My preferred room')
        self.assertEqual(space.bot.context.get('spark.moderators'),
            ['foo.bar@acme.com'])
        self.assertEqual(space.bot.context.get('spark.participants'),
            ['alan.droit@azerty.org'])
        self.assertEqual(space.bot.context.get('spark.team'), None)

        with self.assertRaises(KeyError):  # missing key
            my_bot.context=Context()
            space = SparkSpace(bot=my_bot)
            space.configure({
                'spark': {
                    'moderators':
                        ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                    'participants':
                        ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                    'team': 'Anchor team',
                    'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                    'webhook': "http://73a1e282.ngrok.io",
                }
            })

    def test_configure_2(self):

        logging.info("*** configure/from bot")

        class MySpace(SparkSpace):

            def connect(self):
                assert self.token == '*another bot token'
                self.api = FakeApi()

        my_bot.context = Context()
        space = MySpace(bot=my_bot)
        my_bot.space = space
        os.environ['CHAT_ROOM_TITLE'] = '*my room'
        os.environ['CHAT_ROOM_MODERATORS'] = 'joe.bar@acme.com'
        os.environ['CHAT_TOKEN'] = '*another bot token'

        my_bot.configure()
        self.assertEqual(space.token, '*another bot token')

    def test_lifecycle(self):

        if cisco_spark_bearer is not None:

            logging.info("*** (life cycle)")

            space = SparkSpace(bot=my_bot, ex_token=cisco_spark_bearer)
            space.connect()
            space.bond(title='*transient*for*test')
            self.assertTrue(len(space.id) > 10)
            self.assertEqual(space.title, '*transient*for*test')
            self.assertEqual(space.teamId, None)

            space.post_message('Hello World')

            space.dispose()
            self.assertEqual(space.id, None)
            self.assertEqual(space.title, space.DEFAULT_SPACE_TITLE)
            self.assertEqual(space.team_id, None)

    def test_bond(self):

        logging.info("*** bond")

        space = SparkSpace(bot=my_bot)

        with self.assertRaises(AssertionError):
            space.bond()

        space.api = None
        with self.assertRaises(AssertionError):
            space.bond()

        space.api = FakeApi()
        space.add_moderator = mock.Mock()
        space.add_participant = mock.Mock()

        space.bond(title='*title',
                   moderators=['who', 'knows'],
                   participants=['not', 'me'])

        self.assertTrue(space.add_moderator.called)
        self.assertTrue(space.add_participant.called)

    def test_connect(self):

        logging.info("*** connect")

        class MyAPI(object):
            def __init__(self, access_token):
                self.token = access_token

        def my_factory(access_token):
            return MyAPI(access_token)

        space = SparkSpace(bot=my_bot)
        space.token = None
        space.personal_token = None
        with self.assertRaises(AssertionError):
            space.connect()

        space = SparkSpace(bot=my_bot)
        space.token = 'a'
        space.personal_token = None
        space.connect(factory=my_factory)
        self.assertEqual(space.api.token, 'a')
        self.assertEqual(space.personal_api.token, 'a')

        space = SparkSpace(bot=my_bot)
        space.token = None
        space.personal_token = 'b'
        space.connect(factory=my_factory)
        self.assertEqual(space.api.token, 'b')
        self.assertEqual(space.personal_api.token, 'b')

        space = SparkSpace(bot=my_bot)
        space.token = 'a'
        space.personal_token = 'b'
        space.connect(factory=my_factory)
        self.assertEqual(space.api.token, 'a')
        self.assertEqual(space.personal_api.token, 'b')

    def test_lookup_space(self):

        logging.info("*** lookup_space")

        space = SparkSpace(bot=my_bot)

        with self.assertRaises(AssertionError):
            flag = space.lookup_space(title='*does*not*exist*in*this*world')

        space.api = FakeApi()
        self.assertFalse(space.lookup_space(title='*does*not*exist'))
        self.assertTrue(space.api.rooms.list.called)

        class Intruder(object):
            def list(self):
                raise Exception('TEST')

        space.api.rooms = Intruder()
        self.assertFalse(space.lookup_space(title='any'))

    def test_lookup_space_api(self):

        if cisco_spark_bearer is not None:

            logging.info("*** lookup_space API")

            space = SparkSpace(bot=my_bot, ex_token=cisco_spark_bearer)
            space.connect()

            flag = space.lookup_space(title='*does*not*exist*in*this*world')

            self.assertFalse(flag)

    def test_create_space_mock(self):

        logging.info("*** create_space")

        space = SparkSpace(bot=my_bot)

        with self.assertRaises(AssertionError):
            space.create_space(title='*title')

        space.api = FakeApi()
        space.create_space(title='*title')
        self.assertTrue(space.api.rooms.create.called)
        self.assertEqual(space.title, '*title')
        self.assertEqual(space.id, '*id')

    def test_get_team_mock(self):

        logging.info("*** get_team")

        space = SparkSpace(bot=my_bot)

        class Team(object):
            name = '*name'
            id = '456'

        space.api = FakeApi(teams=[Team()])
        team = space.get_team(name='*name')
        self.assertTrue(space.api.teams.list.called)
        self.assertEqual(team.name, '*name')
        self.assertEqual(team.id, '456')

        space.api = FakeApi(teams=[Team()])
        team = space.get_team(name='*unknown')
        self.assertTrue(space.api.teams.list.called)
        self.assertEqual(team, None)

    def test_add_moderators(self):

        logging.info("*** add_moderators")

        space = SparkSpace(bot=my_bot)
        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator(self):

        logging.info("*** add_moderator")

        space = SparkSpace(bot=my_bot)
        space.api = FakeApi()
        space.id = '*id'

        space.add_moderator(person='foo.bar@acme.com')

        self.assertTrue(space.api.memberships.create.called)

    def test_add_participants(self):

        logging.info("*** add_participants")

        space = SparkSpace(bot=my_bot)
        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant(self):

        logging.info("*** add_participant")
        space = SparkSpace(bot=my_bot)
        space.api = FakeApi()
        space.id = '*id'

        space.add_participant(person='foo.bar@acme.com')

        self.assertTrue(space.api.memberships.create.called)

    def test_delete_space_mock(self):

        logging.info("*** delete_space")
        space = SparkSpace(bot=my_bot)

        # explicit title, room exists
        space.api = FakeApi(rooms=[FakeRoom()])
        space.delete_space(title='*title')
        self.assertTrue(space.api.rooms.delete.called)

        # explicit title, room does not exists
        space.api = FakeApi(rooms=[FakeRoom()])
        space.delete_space(title='*ghost*room')
        self.assertFalse(space.api.rooms.delete.called)

        # bonded room
        space.api = FakeApi(rooms=[FakeRoom()])
        space.id = '*id'
        space.title = '*title'
        space.delete_space()
        self.assertTrue(space.api.rooms.delete.called)

        # configured room, room exists
        space.api = FakeApi(rooms=[FakeRoom()])
        space.id = None
        space.bot.context.set('spark.room', '*title')
        space.delete_space()
        self.assertTrue(space.api.rooms.delete.called)

        # no information
        space.api = FakeApi(rooms=[FakeRoom()])
        space.id = None
        space.bot.context.set('spark.room', None)
        space.delete_space()
        self.assertFalse(space.api.rooms.delete.called)

    def test_dispose_mock(self):

        logging.info("*** dispose")
        space = SparkSpace(bot=my_bot)
        space.api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')

        space.dispose()

        self.assertTrue(space.api.rooms.delete.called)

    def test_post_message_mock(self):

        logging.info("*** post_message")
        space = SparkSpace(bot=my_bot)

        space.api = FakeApi()
        space.post_message(text='hello world')
        self.assertTrue(space.api.messages.create.called)

        space.api = FakeApi()
        space.post_message(content='hello world')
        self.assertTrue(space.api.messages.create.called)

        try:
            space.api = FakeApi()
            space.post_message(text='hello world',
                               content='hello world',
                               file='./test_messages/sample.png')
            self.assertTrue(space.api.messages.create.called)
        except IOError:
            pass

    def test_register_mock(self):

        logging.info("*** register")
        space = SparkSpace(bot=my_bot)

        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')
        space.register('*hook')
        self.assertTrue(space.personal_api.webhooks.create.called)

    def test_on_run(self):

        logging.info("*** on_run")
        space = SparkSpace(bot=my_bot)
        space.api = FakeApi()
        space.personal_api = FakeApi()
        space.on_run()
        self.assertTrue(space.api.people.me.called)
        self.assertTrue(space.personal_api.people.me.called)

        if cisco_spark_bearer is not None:

            logging.info("*** on_run API")

            space = SparkSpace(bot=my_bot, bearer=cisco_spark_bearer)
            space.connect()
            item = space.on_run()
            self.assertTrue(my_bot.context.get('bot.id') > 20)

    def test_work(self):

        logging.info("*** work")
        my_bot.context = Context()
        space = SparkSpace(bot=my_bot)
        space.api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')

        space.PULL_INTERVAL = 0.001
        mocked = mock.Mock(return_value=[])
        space.pull = mocked

        p = Process(target=space.work)
        p.daemon = True
        p.start()

        p.join(0.01)
        if p.is_alive():
            logging.info('Stopping puller')
            my_bot.context.set('general.switch', 'off')
            p.join()

        self.assertFalse(p.is_alive())

    def test_webhook(self):

        logging.info("*** webhook")
        space = SparkSpace(bot=my_bot)

        space.personal_api = FakeApi()
        my_bot.ears = Queue()
        self.assertEqual(space.webhook(message_id='*123'), 'OK')
        self.assertTrue(space.personal_api.messages.get.called)
        self.assertEqual(yaml.safe_load(my_bot.ears.get()),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'space_id': None,
                          'type': 'message',
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(my_bot.ears.get_nowait())

    def test_pull(self):

        logging.info("*** pull")
        my_bot.context = Context()
        my_bot.ears = Queue()
        space = SparkSpace(bot=my_bot)
        space.api = FakeApi(messages=[FakeMessage()])
        space.bond(title='*title')

        self.assertEqual(space._last_message_id, 0)
        space.pull()
        self.assertEqual(my_bot.context.get('puller.counter'), 1)
        self.assertTrue(space.api.messages.list.called)
        self.assertEqual(space._last_message_id, '*id')

        space.pull()
        self.assertEqual(my_bot.context.get('puller.counter'), 2)
        self.assertEqual(space._last_message_id, '*id')

        space.pull()
        self.assertEqual(my_bot.context.get('puller.counter'), 3)
        self.assertEqual(space._last_message_id, '*id')

        self.assertEqual(yaml.safe_load(my_bot.ears.get()),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'space_id': None,
                          'type': 'message',
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(my_bot.ears.get_nowait())

    def test_on_message(self):

        logging.info("*** on_message")
        space = SparkSpace(bot=my_bot)

        space.on_message(my_message, my_queue)
        message = my_message.copy()
        message.update({"type": "message"})
        message.update({"content": message['text']})
        message.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY'})
        message.update({"from_label": 'matt@example.com'})
        message.update({"mentioned_ids": ['Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM',
                       'Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg']})
        message.update({"space_id": 'Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(my_queue.get()), message)

        attachment = my_message.copy()
        attachment.update({"type": "attachment"})
        attachment.update({"url": "http://www.example.com/images/media.png"})
        attachment.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY'})
        attachment.update({"from_label": 'matt@example.com'})
        attachment.update({"space_id": 'Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0'})
        self.assertEqual(yaml.safe_load(my_queue.get()), attachment)

        with self.assertRaises(Exception):
            print(my_queue.get_nowait())

    def test_download_attachment(self):

        logging.info("*** download_attachment")

        class MySpace(SparkSpace):
            def name_attachment(self, url):
                return 'some_file.pdf'

            def get_attachment(self, url):
                return b'hello world'

        space = MySpace(bot=my_bot)
        outcome = space.download_attachment(url='/dummy')

        with open(outcome, "r+b") as handle:
            self.assertEqual(handle.read(), space.get_attachment('/dummy'))

        try:
            os.remove(outcome)
        except:
            pass

    def test_name_attachment(self):

        logging.info("*** name_attachment")

        class MyResponse(object):
            def __init__(self, status_code=200, headers={}):
                self.status_code = status_code
                self.headers = headers

        space = SparkSpace(bot=my_bot)

        space.personal_token = '*void'
        space.token = None
        response = MyResponse(headers={'Content-Disposition': 'who cares'})
        self.assertEqual(space.name_attachment(url='/dummy', response=response),
                         'downloadable')

        space.personal_token = None
        space.token = '*void'
        response = MyResponse(headers={'Content-Disposition': 'filename="some_file.pdf"'})
        self.assertEqual(space.name_attachment(url='/dummy', response=response),
                         'some_file.pdf')

        space.personal_token = None
        space.token = None
        response = MyResponse(status_code=400, headers={'Content-Disposition': 'filename="some_file.pdf"'})
        with self.assertRaises(Exception):
            name = space.name_attachment(url='/dummy', response=response)

    def test_get_attachment(self):

        logging.info("*** get_attachment")

        class MyResponse(object):
            def __init__(self, status_code=200, headers={}):
                self.status_code = status_code
                self.headers = headers
                self.encoding = 'encoding'
                self.content = 'content'

        space = SparkSpace(bot=my_bot)

        space.personal_token = '*void'
        space.token = None
        response = MyResponse(headers={})
        self.assertEqual(space.get_attachment(url='/dummy', response=response),
                         'content')

        space.personal_token = None
        space.token = '*void'
        response = MyResponse(headers={})
        self.assertEqual(space.get_attachment(url='/dummy', response=response),
                         'content')

        space.personal_token = None
        space.token = None
        response = MyResponse(status_code=400, headers={})
        with self.assertRaises(Exception):
            name = space.get_attachment(url='/dummy', response=response)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
