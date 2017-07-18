#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from bottle import request
import gc
import json
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
import yaml

from shellbot import Context
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
    isLocked = True
    title = '*title'
    type = 'group'
    teamId = '*team'


class FakeTeamRoom(Fake):
    id = '*team_id'
    isLocked = True
    title = '*team_title'
    type = 'team'
    teamId = None


class FakeMessage(Fake):
    id = '*id'
    message = '*message'
    _json = {'text': '*message'}


class FakeBot(Fake):
    displayName = "shelly"
    created = "2017-04-21T12:16:20.292Z"
    emails = ["shelly@sparkbot.io"]
    orgId = "Y2lzY29zcGFyazoMTk4ZjA4YS0zODgwLTQ4NzEtYjU1ZS00ODYzY2NmNzIzZDU"
    avatar = "https://2b571e19c5.rackcdn.com/V1~5957fdf80TZekRY3-49nfcA==~80"
    type = "bot"
    id = "Y2lzY29zcGFyazovL3VztOGFiOS01ZGI5M2Y5MjI5MWM"


class FakePerson(Fake):
    status = "active"
    nickName = "Foo"
    displayName = "Foo Bar"
    firstName = "Foo"
    lastName = "Bar"
    created = "2017-04-21T12:16:20.292Z"
    lastActivity = "2017-04-21T12:16:20.292Z"
    emails = ["foo.bar@acme.com"]
    orgId = "Y2lzY29zcGFyazoMTk4ZjA4YS0zODgwLTQ4NzEtYjU1ZS00ODYzY2NmNzIzZDU"
    avatar = "https://2b571e19c5.rackcdn.com/V1~5957fdf80TZekRY3-49nfcA==~80"
    type = "person"
    id = 'Y2lzY29zcGFyazovL3VzL1RFQU0Yy0xMWU2LWE5ZDgtMjExYTBkYzc5NzY5'


class FakeApi(object):

    def __init__(self,
                 access_token=None,
                 rooms=[],
                 new_room=None,
                 teams=[],
                 messages=[],
                 me=FakePerson()):

        self.token = access_token

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
        self.memberships.delete = mock.Mock()

        self.messages = Fake()
        self.messages.list = mock.Mock(return_value=messages)
        self.messages.create = mock.Mock(return_value=FakeMessage())
        self.messages.delete = mock.Mock()
        self.messages.get = mock.Mock(return_value=FakeMessage())

        self.webhooks = Fake()
        self.webhooks.list = mock.Mock(return_value=[])
        self.webhooks.create = mock.Mock()

        self.people = Fake()
        self.people.me = mock.Mock(return_value=me)


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

    def setUp(self):
        self.context = Context()
        self.ears = Queue()

    def tearDown(self):
        del self.ears
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("*** init")

        space = SparkSpace(context=self.context, token='b')
        self.assertEqual(space.get('token'), 'b')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space.teamId, None)

        space = SparkSpace(context=self.context, token='b', personal_token='c')
        self.assertEqual(space.get('token'), 'b')
        self.assertEqual(space.get('personal_token'), 'c')

    def test_is_ready(self):

        logging.info("*** is_ready")

        space = SparkSpace(context=self.context)
        self.assertFalse(space.is_ready)

        space = Space(context=Context(settings={'space.id': '123'}))
        self.assertTrue(space.is_ready)

        space = Space(context=self.context)
        space.values['id'] = '*id'
        self.assertTrue(space.is_ready)

    def test_configure(self):

        logging.info("*** configure")

        space = SparkSpace(context=self.context)
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
        self.assertEqual(space.get('token'), 'hkNWEtMJNkODVGlZWU1NmYtyY')
        self.assertEqual(space.get('personal_token'), '*personal*secret*token')
        self.assertEqual(space.id, None)   #  set after bond()
        self.assertEqual(space.title, None)
        self.assertEqual(space.teamId, None)

        self.context.clear()
        space = SparkSpace(context=self.context)
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

        self.assertEqual(space.context.get('spark.room'), 'My preferred room')
        self.assertEqual(space.context.get('spark.moderators'),
            ['foo.bar@acme.com', 'joe.bar@corporation.com'])
        self.assertEqual(space.context.get('spark.participants'),
            ['alan.droit@azerty.org', 'bob.nard@support.tv'])
        self.assertEqual(space.context.get('spark.team'), 'Anchor team')

        self.context.clear()
        space = SparkSpace(context=self.context)
        space.configure({
            'spark': {
                'room': 'My preferred room',
                'moderators': 'foo.bar@acme.com',
                'participants': 'alan.droit@azerty.org',
            }
        })
        self.assertEqual(space.context.get('spark.room'), 'My preferred room')
        self.assertEqual(space.context.get('spark.moderators'),
            ['foo.bar@acme.com'])
        self.assertEqual(space.context.get('spark.participants'),
            ['alan.droit@azerty.org'])
        self.assertEqual(space.context.get('spark.team'), None)

        with self.assertRaises(KeyError):  # missing key
            self.context.clear()
            space = SparkSpace(context=self.context)
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

    def test_lifecycle(self):

        if cisco_spark_bearer is not None:

            logging.info("*** (life cycle)")

            space = SparkSpace(context=self.context, ex_token=cisco_spark_bearer)
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

        space = SparkSpace(context=self.context)

        with self.assertRaises(AssertionError):
            space.bond()

        space.api = None
        with self.assertRaises(AssertionError):
            space.bond()

        space.api = FakeApi()

        space.personal_api = None
        with self.assertRaises(AssertionError):
            space.bond()

        space.personal_api = FakeApi()

        space.add_moderator = mock.Mock()
        space.add_participant = mock.Mock()
        space.del_participant = mock.Mock()

        space.bond(title='*title',
                   moderators=['who', 'knows'],
                   participants=['not', 'me'])

        self.assertTrue(space.add_moderator.called)
        self.assertTrue(space.add_participant.called)
        self.assertTrue(space.del_participant('joe.bar@acme.com'))

    def test_connect(self):

        logging.info("*** connect")

        def my_factory(access_token):
            return FakeApi(access_token=access_token)

        space = SparkSpace(context=self.context)
        space.set('token', None)
        space.set('personal_token', None)
        with self.assertRaises(AssertionError):
            space.connect()

        space = SparkSpace(context=self.context)
        space.set('token', 'a')
        space.set('personal_token', None)
        space.connect(factory=my_factory)
        self.assertEqual(space.api.token, 'a')
        self.assertEqual(space.personal_api.token, 'a')

        space = SparkSpace(context=self.context)
        space.set('token', None)
        space.set('personal_token', 'b')
        space.connect(factory=my_factory)
        self.assertEqual(space.api.token, 'b')
        self.assertEqual(space.personal_api.token, 'b')

        space = SparkSpace(context=self.context)
        space.set('token', 'a')
        space.set('personal_token', 'b')
        space.connect(factory=my_factory)
        self.assertEqual(space.api.token, 'a')
        self.assertEqual(space.personal_api.token, 'b')

    def test_is_ready(self):

        logging.info("*** is_ready")

        space = SparkSpace(context=self.context)
        self.assertFalse(space.is_ready)

        space.values['id'] = '*id'
        self.assertTrue(space.is_ready)

    def test_id(self):

        logging.info("*** id")

        space = SparkSpace(context=self.context)
        self.assertTrue(space.id is None)

        space.values['id'] = '*id'
        self.assertEqual(space.id, '*id')

    def test_use_space(self):

        logging.info("*** use_space")

        space = SparkSpace(context=self.context)

        with self.assertRaises(AssertionError):
            flag = space.use_space(id='*no*api*anyway')

        space.personal_api = FakeApi(rooms=[FakeRoom()])
        self.assertFalse(space.use_space(id='*does*not*exist'))
        self.assertTrue(space.personal_api.rooms.list.called)

        self.assertTrue(space.use_space(id='*id'))

        class Intruder(object):
            def list(self):
                raise Exception('TEST')

        space.personal_api.rooms = Intruder()
        self.assertFalse(space.use_space(id='any'))

    def test_lookup_space(self):

        logging.info("*** lookup_space")

        space = SparkSpace(context=self.context)

        with self.assertRaises(AssertionError):
            flag = space.use_space(id='*no*api*anyway')

        space.personal_api = FakeApi(rooms=[FakeRoom()])
        self.assertFalse(space.lookup_space(title='*does*not*exist'))
        self.assertTrue(space.personal_api.rooms.list.called)

        self.assertTrue(space.lookup_space(title='*title'))

        class Intruder(object):
            def list(self):
                raise Exception('TEST')

        space.personal_api.rooms = Intruder()
        self.assertFalse(space.lookup_space(title='any'))

    def test_lookup_space_api(self):

        if cisco_spark_bearer is not None:

            logging.info("*** lookup_space API")

            space = SparkSpace(context=self.context, ex_token=cisco_spark_bearer)
            space.connect()

            flag = space.lookup_space(title='*does*not*exist*in*this*world')

            self.assertFalse(flag)

    def test_create_space(self):

        logging.info("*** create_space")

        space = SparkSpace(context=self.context)

        with self.assertRaises(AssertionError):
            space.create_space(title='*title')

        space.personal_api = FakeApi()
        space.create_space(title='*title')
        self.assertTrue(space.personal_api.rooms.create.called)
        self.assertEqual(space.title, '*title')
        self.assertEqual(space.id, '*id')

    def test_use_room(self):

        logging.info("*** use_room")

        self.context.set('bot.email', 'a@acme.com')
        self.context.set('administrator.email', 'b@acme.com')
        space = SparkSpace(context=self.context)
        space.add_moderator = mock.Mock()

        space.use_room(room=FakeRoom())
        self.assertEqual(space.id, '*id')
        self.assertEqual(space.title, '*title')
        self.assertFalse(space.is_direct)
        self.assertTrue(space.is_group)
        self.assertFalse(space.is_team)
        self.assertTrue(space.is_locked)
        self.assertEqual(space.team_id, '*team')
        space.add_moderator.assert_called_with('a@acme.com')

        space.use_room(room=FakeTeamRoom())
        self.assertEqual(space.id, '*team_id')
        self.assertEqual(space.title, '*team_title')
        self.assertFalse(space.is_direct)
        self.assertTrue(space.is_group)
        self.assertTrue(space.is_team)
        self.assertTrue(space.is_locked)
        self.assertEqual(space.team_id, None)
        space.add_moderator.assert_called_with('a@acme.com')

    def test_get_team(self):

        logging.info("*** get_team")

        space = SparkSpace(context=self.context)

        class Team(object):
            name = '*name'
            id = '456'

        space.personal_api = FakeApi(teams=[Team()])
        team = space.get_team(name='*name')
        self.assertTrue(space.personal_api.teams.list.called)
        self.assertEqual(team.name, '*name')
        self.assertEqual(team.id, '456')

        space.personal_api = FakeApi(teams=[Team()])
        team = space.get_team(name='*unknown')
        self.assertTrue(space.personal_api.teams.list.called)
        self.assertEqual(team, None)

    def test_add_moderators(self):

        logging.info("*** add_moderators")

        space = SparkSpace(context=self.context)
        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator(self):

        logging.info("*** add_moderator")

        space = SparkSpace(context=self.context)
        space.personal_api = FakeApi()
        space.values['id'] = '*id'

        space.add_moderator(person='foo.bar@acme.com')

        self.assertTrue(space.personal_api.memberships.create.called)

    def test_add_participants(self):

        logging.info("*** add_participants")

        space = SparkSpace(context=self.context)
        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant(self):

        logging.info("*** add_participant")
        space = SparkSpace(context=self.context)
        space.personal_api = FakeApi()
        space.values['id'] = '*id'

        space.add_participant(person='foo.bar@acme.com')

        self.assertTrue(space.personal_api.memberships.create.called)

    def test_remove_participant(self):

        logging.info("*** remove_participant")
        space = SparkSpace(context=self.context)
        space.personal_api = FakeApi()
        space.values['id'] = '*id'

        space.remove_participant(person='foo.bar@acme.com')

        self.assertTrue(space.personal_api.memberships.delete.called)

    def test_delete_space(self):

        logging.info("*** delete_space")
        space = SparkSpace(context=self.context)

        # explicit title, room exists
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.delete_space(title='*title')
        self.assertTrue(space.personal_api.rooms.delete.called)

        # explicit title, room does not exists
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.delete_space(title='*ghost*room')
        self.assertFalse(space.personal_api.rooms.delete.called)

        # bonded room
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.values['id'] = '*id'
        space.values['title'] = '*title'
        space.delete_space()
        self.assertTrue(space.personal_api.rooms.delete.called)

        # configured room, room exists
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.values['id'] = None
        self.context.set('spark.room', '*title')
        space.delete_space()
        self.assertTrue(space.personal_api.rooms.delete.called)

        # no information
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.values['id'] = None
        self.context.set('spark.room', None)
        space.delete_space()
        self.assertFalse(space.personal_api.rooms.delete.called)

    def test_dispose(self):

        logging.info("*** dispose")
        space = SparkSpace(context=self.context)
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')

        space.dispose()

        self.assertTrue(space.personal_api.rooms.delete.called)

    def test_post_message(self):

        logging.info("*** post_message")
        space = SparkSpace(context=self.context)

        space.api = FakeApi()
        space.post_message(text='hello world')
        self.assertTrue(space.api.messages.create.called)

        space.api = FakeApi()
        space.post_message(content='hello world')
        self.assertTrue(space.api.messages.create.called)

        space.api = FakeApi()
        space.post_message(text='hello world',
                           content='hello world',
                           file='./test_messages/sample.png',
                           space_id=None)
        self.assertTrue(space.api.messages.create.called)

        space.api = FakeApi()
        space.post_message(text='hello world',
                           content='hello world',
                           file='./test_messages/sample.png',
                           space_id='123')
        self.assertTrue(space.api.messages.create.called)

    def test_register(self):

        logging.info("*** register")
        space = SparkSpace(context=self.context)

        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        self.context.set('bot.id', '*id')
        space.bond(title='*title')
        space.register('*hook')
        self.assertTrue(space.personal_api.webhooks.create.called)

    def test_on_connect(self):

        logging.info("*** on_connect")
        space = SparkSpace(context=self.context)
        space.api = FakeApi(me=FakeBot())
        space.personal_api = FakeApi(me=FakePerson())
        space.on_connect()
        self.assertTrue(space.api.people.me.called)
        self.assertTrue(space.personal_api.people.me.called)
        self.assertEqual(self.context.get('bot.email'), 'shelly@sparkbot.io')
        self.assertEqual(self.context.get('bot.name'), 'shelly')
        self.assertTrue(len(self.context.get('bot.id')) > 20)
        self.assertEqual(self.context.get('administrator.email'), 'foo.bar@acme.com')
        self.assertEqual(self.context.get('administrator.name'), 'Foo Bar')
        self.assertTrue(len(self.context.get('administrator.id')) > 20)

    def test_run(self):

        logging.info("*** run")
        space = SparkSpace(context=self.context)
        space.api = FakeApi(rooms=[FakeRoom()])
        space.personal_api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')

        space.PULL_INTERVAL = 0.001
        mocked = mock.Mock(return_value=[])
        space.pull = mocked

        p = space.start()
        p.join(0.01)
        if p.is_alive():
            logging.info('Stopping puller')
            self.context.set('general.switch', 'off')
            p.join()

        self.assertFalse(p.is_alive())

    def test_webhook(self):

        logging.info("*** webhook")
        space = SparkSpace(context=self.context, ears=self.ears)

        space.personal_api = FakeApi()
        self.assertEqual(space.webhook(message_id='*123'), 'OK')
        self.assertTrue(space.personal_api.messages.get.called)
        data = self.ears.get()
        self.assertEqual(yaml.safe_load(data),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'injection',
                          'space_id': None,
                          'type': 'message',
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_pull(self):

        logging.info("*** pull")
        space = SparkSpace(context=self.context, ears=self.ears)
        space.api = FakeApi(messages=[FakeMessage()])
        space.personal_api = FakeApi(messages=[FakeMessage()])
        space.bond(title='*title')

        self.assertEqual(space._last_message_id, 0)
        space.pull()
        self.assertEqual(self.context.get('puller.counter'), 1)
        self.assertTrue(space.api.messages.list.called)
        self.assertEqual(space._last_message_id, '*id')

        space.pull()
        self.assertEqual(self.context.get('puller.counter'), 2)
        self.assertEqual(space._last_message_id, '*id')

        space.pull()
        self.assertEqual(self.context.get('puller.counter'), 3)
        self.assertEqual(space._last_message_id, '*id')

        self.assertEqual(yaml.safe_load(self.ears.get()),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'pull',
                          'space_id': None,
                          'type': 'message',
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_on_message(self):

        logging.info("*** on_message")
        space = SparkSpace(context=self.context)

        space.on_message(my_message, self.ears)
        message = my_message.copy()
        message.update({"type": "message"})
        message.update({"content": message['text']})
        message.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY'})
        message.update({"from_label": 'matt@example.com'})
        message.update({"mentioned_ids": ['Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM',
                       'Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg']})
        message.update({"space_id": 'Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), message)

        attachment = my_message.copy()
        attachment.update({"type": "attachment"})
        attachment.update({"url": "http://www.example.com/images/media.png"})
        attachment.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY'})
        attachment.update({"from_label": 'matt@example.com'})
        attachment.update({"space_id": 'Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0'})
        self.assertEqual(yaml.safe_load(self.ears.get()), attachment)

        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_download_attachment(self):

        logging.info("*** download_attachment")

        class MySpace(SparkSpace):
            def name_attachment(self, url):
                return 'some_file.pdf'

            def get_attachment(self, url):
                return b'hello world'

        space = MySpace(context=self.context)
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

        space = SparkSpace(context=self.context)

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

        space = SparkSpace(context=self.context)

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
