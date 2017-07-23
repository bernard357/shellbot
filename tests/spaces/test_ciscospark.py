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
from shellbot.channel import Channel
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


class FakeDirectRoom(Fake):
    id = '*direct_id'
    isLocked = False
    title = 'Marcel Jones'
    type = 'direct'
    lastActivity = "2017-07-22T22:34:22.969Z"
    creatorId = "Y2lzY29zcGFyazovL3VzL1BFT1zQtYTIyYi1mYWYwZWQwMjkyMzU"
    created = "2017-07-19T05:29:23.962Z"


class FakeTeamRoom(Fake):
    id = '*team_id'
    isLocked = True
    title = '*team_title'
    type = 'team'
    teamId = None


class FakeChannel(object):
    id = '*123'
    title = '*title'
    is_direct = False
    is_moderated = False


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
                 room=FakeRoom(),
                 teams=[],
                 messages=[],
                 me=FakePerson()):

        self.token = access_token

        self.rooms = Fake()
        self.rooms.list = mock.Mock(return_value=rooms if rooms else [room])
        self.rooms.get = mock.Mock(return_value=room)
        self.rooms.create = mock.Mock(return_value=room)
        self.rooms.update = mock.Mock()
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

my_private_message = {
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NB0xMWU3LTljODctNTljZjJjNDRhYmIy",
    "roomId": "Y2lzY29zcGFyazovL3VzL1JP0zY2VmLWJiNDctOTZlZjA1NmJhYzFl",
    "roomType": "direct",
    "text": "test",
    "created": "2017-07-22T16:49:22.008Z",
    "hook": "shellbot-messages",
    "personEmail": "foo.bar@again.org",
    "personId": "Y2lzY29zcGFyazovL3VzL1LTQ5YzQtYTIyYi1mYWYwZWQwMjkyMzU",
}

my_join = {
    'isMonitor': False,
    'created': '2017-05-31T21:25:30.424Z',
    'personId': 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U',
    'isModerator': False,
    'personOrgId': 'Y2lzY29zcGFyazovL3V0FOSVpBVElPTi9jb25zdW1lcg',
    'personDisplayName': 'Foo Bar',
    'personEmail': 'foo.bar@acme.com',
    'roomId': 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz',
    'id': 'Y2lzY29zcGFyazovL3VzDctMTFlNy05OTAwLTA1OTAyNmIwYjQ1Mw'
}

my_leave = {
    'isMonitor': False,
    'created': '2017-05-31T21:25:30.424Z',
    'personId': 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U',
    'isModerator': False,
    'personOrgId': 'Y2lzY29zcGFyazovL3V0FOSVpBVElPTi9jb25zdW1lcg',
    'personDisplayName': 'Foo Bar',
    'personEmail': 'foo.bar@acme.com',
    'roomId': 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz',
    'id': 'Y2lzY29zcGFyazovL3VzDctMTFlNy05OTAwLTA1OTAyNmIwYjQ1Mw'
}


class SparkSpaceTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.ears = Queue()
        self.space = SparkSpace(context=self.context, ears=self.ears)

    def tearDown(self):
        del self.space
        del self.ears
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_on_init(self):

        logging.info("*** on_init")

        self.assertEqual(self.space.prefix, 'spark')
        self.assertEqual(self.space.get('token'), None)
        self.assertEqual(self.space.get('personal_token'), None)
        self.assertEqual(self.space.api, None)
        self.assertEqual(self.space.personal_api, None)
        self.assertEqual(self.space.teamId, None)
        self.assertEqual(self.space._last_message_id, 0)

        space = SparkSpace(context=self.context, token='b', personal_token='c')
        self.assertEqual(space.get('token'), 'b')
        self.assertEqual(space.get('personal_token'), 'c')

    def test_configure(self):

        logging.info("*** configure")

        settings={  # from settings to member attributes
            'spark': {
                'room': 'My preferred room',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
                'personal_token': '*personal*secret*token',
            }
        }
        self.space.configure(settings=settings)
        self.assertEqual(self.space.get('room'), 'My preferred room')
        self.assertEqual(self.space.configured_title(), 'My preferred room')
        self.assertEqual(self.space.get('participants'),
            ['alan.droit@azerty.org', 'bob.nard@support.tv'])
        self.assertEqual(self.space.get('token'), 'hkNWEtMJNkODVGlZWU1NmYtyY')
        self.assertEqual(self.space.get('personal_token'), '*personal*secret*token')

        self.space.context.clear()
        self.space.configure({
            'spark': {
                'room': 'My preferred room',
                'participants': 'alan.droit@azerty.org',
            }
        })
        self.assertEqual(self.space.get('room'), 'My preferred room')
        self.assertEqual(self.space.get('participants'),
            ['alan.droit@azerty.org'])

        with self.assertRaises(KeyError):  # missing key
            self.space.context.clear()
            self.space.configure({
                'spark': {
                    'participants':
                        ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                    'team': 'Anchor team',
                    'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                }
            })

    def test_connect(self):

        logging.info("*** connect")

        def my_factory(access_token):
            return FakeApi(access_token=access_token)

        self.space.set('token', None)
        self.space.set('personal_token', None)
        with self.assertRaises(AssertionError):
            self.space.connect()

        self.space.set('token', 'a')
        self.space.set('personal_token', None)
        self.space.connect(factory=my_factory)
        self.assertEqual(self.space.api.token, 'a')
        self.assertEqual(self.space.personal_api.token, 'a')

        self.space.set('token', None)
        self.space.set('personal_token', 'b')
        self.space.connect(factory=my_factory)
        self.assertEqual(self.space.api.token, 'b')
        self.assertEqual(self.space.personal_api.token, 'b')

        self.space.set('token', 'a')
        self.space.set('personal_token', 'b')
        self.space.connect(factory=my_factory)
        self.assertEqual(self.space.api.token, 'a')
        self.assertEqual(self.space.personal_api.token, 'b')

    def test_on_connect(self):

        logging.info("*** on_connect")

        self.space.api = FakeApi(me=FakeBot())
        self.space.personal_api = FakeApi(me=FakePerson())
        self.space.on_connect()
        self.assertTrue(self.space.api.people.me.called)
        self.assertTrue(self.space.personal_api.people.me.called)
        self.assertEqual(self.context.get('bot.email'), 'shelly@sparkbot.io')
        self.assertEqual(self.context.get('bot.name'), 'shelly')
        self.assertTrue(len(self.context.get('bot.id')) > 20)
        self.assertEqual(self.context.get('administrator.email'), 'foo.bar@acme.com')
        self.assertEqual(self.context.get('administrator.name'), 'Foo Bar')
        self.assertTrue(len(self.context.get('administrator.id')) > 20)

    def test_create(self):

        logging.info("*** create")

        with self.assertRaises(AssertionError):
            self.space.create(title=None)

        with self.assertRaises(AssertionError):
            self.space.create(title='')

        with self.assertRaises(AssertionError):
            self.space.create(title='*title')

        self.space.personal_api = FakeApi()
        channel = self.space.create(title='*title')
        self.assertTrue(self.space.personal_api.rooms.create.called)
        self.assertEqual(channel.id, '*id')
        self.assertEqual(channel.title, '*title')

    def test_get_by_title(self):

        logging.info("*** get_by_title")

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_title(None)

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_title('')

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_title('*no*api*anyway')

        self.space.personal_api = FakeApi()
        channel = self.space.get_by_title('*does*not*exist')
        self.assertEqual(channel, None)
        self.assertTrue(self.space.personal_api.rooms.list.called)

        channel = self.space.get_by_title('*title')
        self.assertEqual(
            channel,
            Channel({
                "id": "*id",
                "is_direct": False,
                "is_group": True,
                "is_moderated": True,
                "is_team": False,
                "team_id": "*team",
                "title": "*title",
                "type": "group",
            }))

        class Intruder(object):
            def list(self, **kwargs):
                raise Exception('TEST')

        self.space.personal_api.rooms = Intruder()
        channel = self.space.get_by_title('*title')
        self.assertEqual(channel, None)

    def test_get_by_id(self):

        logging.info("*** get_by_id")

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_id(None)

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_id('')

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_id('*no*api*anyway')

        self.space.personal_api = FakeApi()

        channel = self.space.get_by_id('*id')
        self.assertEqual(
            channel,
            Channel({
                "id": "*id",
                "is_direct": False,
                "is_group": True,
                "is_moderated": True,
                "is_team": False,
                "team_id": "*team",
                "title": "*title",
                "type": "group",
            }))

        class Intruder(object):
            def get(self, label, **kwargs):
                raise Exception('TEST')

        self.space.personal_api.rooms = Intruder()
        channel = self.space.get_by_id('*id')
        self.assertEqual(channel, None)

    def test_get_by_person(self):

        logging.info("*** get_by_person")

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_person(None)

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_person('')

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_person('*no*api*anyway')

        self.space.api = FakeApi(room=FakeDirectRoom())

        channel = self.space.get_by_person('Marcel Jones')
        self.assertEqual(
            channel,
            Channel({
                "id": "*direct_id",
                "is_direct": True,
                "is_group": False,
                "is_moderated": False,
                "is_team": False,
                "team_id": None,
                "title": "Marcel Jones",
                "type": "direct",
            }))

        class Intruder(object):
            def list(self, **kwargs):
                raise Exception('TEST')

        self.space.api.rooms = Intruder()
        channel = self.space.get_by_person('Marcel Jones')
        self.assertEqual(channel, None)

    def test_update(self):

        logging.info("*** update")

        self.space.api = FakeApi()
        self.space.update(channel=FakeChannel())

    def test_delete(self):

        logging.info("*** delete")


        # explicit id, room exists
        self.space.api = FakeApi()
        self.space.personal_api = FakeApi()
        self.space.delete(id='*id')
        self.assertTrue(self.space.personal_api.rooms.delete.called)

        # explicit id, room does not exists
        self.space.api = FakeApi()
        self.space.personal_api = FakeApi()
        self.space.delete(id='*ghost*room')
        self.assertTrue(self.space.personal_api.rooms.delete.called)

    def test_get_team(self):

        logging.info("*** get_team")

        class Team(object):
            name = '*name'
            id = '456'

        self.space.personal_api = FakeApi(teams=[Team()])
        team = self.space.get_team(name='*name')
        self.assertTrue(self.space.personal_api.teams.list.called)
        self.assertEqual(team.name, '*name')
        self.assertEqual(team.id, '456')

        self.space.personal_api = FakeApi(teams=[Team()])
        team = self.space.get_team(name='*unknown')
        self.assertTrue(self.space.personal_api.teams.list.called)
        self.assertEqual(team, None)

    def test_add_participants(self):

        logging.info("*** add_participants")

        with mock.patch.object(self.space,
                               'add_participant') as mocked:

            self.space.add_participants(id='*id', persons=['foo.bar@acme.com'])
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_add_participant(self):

        logging.info("*** add_participant")

        self.space.personal_api = FakeApi()
        self.space.add_participant(id='*id', person='foo.bar@acme.com')
        self.assertTrue(self.space.personal_api.memberships.create.called)

    def test_remove_participants(self):

        logging.info("*** remove_participants")

        with mock.patch.object(self.space,
                               'remove_participant') as mocked:

            self.space.remove_participants(id='*id', persons=['foo.bar@acme.com'])
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_remove_participant(self):

        logging.info("*** remove_participant")

        self.space.personal_api = FakeApi()
        self.space.remove_participant(id='*id', person='foo.bar@acme.com')
        self.assertTrue(self.space.personal_api.memberships.delete.called)

    def test_post_message(self):

        logging.info("*** post_message")

        self.space.api = FakeApi()
        self.space.post_message(id='*id', text='hello world')
        self.assertTrue(self.space.api.messages.create.called)

        self.space.api = FakeApi()
        self.space.post_message(person='a@b.com', text='hello world')
        self.assertTrue(self.space.api.messages.create.called)

        self.space.api = FakeApi()
        self.space.post_message(id='*id', content='hello world')
        self.assertTrue(self.space.api.messages.create.called)

        self.space.api = FakeApi()
        self.space.post_message(person='a@b.com', content='hello world')
        self.assertTrue(self.space.api.messages.create.called)

        self.space.api = FakeApi()
        with self.assertRaises(AssertionError):
            self.space.post_message(
                text='hello world',
                content='hello world',
                file='./test_messages/sample.png')

        self.space.api = FakeApi()
        with self.assertRaises(AssertionError):
            self.space.post_message(
                id='*id',
                person='a@b.com',
                text='hello world',
                content='hello world',
                file='./test_messages/sample.png')

        self.space.api = FakeApi()
        self.space.post_message(
            id='*id',
            text='hello world',
            content='hello world',
            file='./test_messages/sample.png')
        self.assertTrue(self.space.api.messages.create.called)

        self.space.api = FakeApi()
        self.space.post_message(
            person='a@b.com',
            text='hello world',
            content='hello world',
            file='./test_messages/sample.png')
        self.assertTrue(self.space.api.messages.create.called)

    def test_register(self):

        logging.info("*** register")

        self.space.api = FakeApi()
        self.space.personal_api = FakeApi()
        self.context.set('bot.id', '*id')
        self.context.set('spark.token', '*token')
        self.context.set('spark.personal_token', '*token')
        self.space.register('*hook')
        self.assertTrue(self.space.api.webhooks.create.called)
        self.assertTrue(self.space.personal_api.webhooks.create.called)

    def test_deregister(self):

        logging.info("*** deregister")

        self.space.api = FakeApi()
        self.space.personal_api = FakeApi()
        self.context.set('bot.id', '*id')
        self.space.deregister()
        self.assertTrue(self.space.api.webhooks.list.called)
        self.assertTrue(self.space.personal_api.webhooks.list.called)

    def test_run(self):

        logging.info("*** run")

        self.space.api = FakeApi()
        self.space.personal_api = FakeApi()

        self.space.PULL_INTERVAL = 0.001
        mocked = mock.Mock(return_value=[])
        self.space.pull = mocked

        p = self.space.start()
        p.join(0.01)
        if p.is_alive():
            logging.info('Stopping puller')
            self.context.set('general.switch', 'off')
            p.join()

        self.assertFalse(p.is_alive())

    def test_webhook(self):

        logging.info("*** webhook")

        self.space.personal_api = FakeApi()
        self.assertEqual(self.space.webhook(message_id='*123'), 'OK')
        self.assertTrue(self.space.personal_api.messages.get.called)
        data = self.space.ears.get()
        self.assertEqual(yaml.safe_load(data),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'injection',
                          'channel_id': None,
                          'type': 'message',
                          'is_direct': False,
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_pull(self):

        logging.info("*** pull")

        self.space.api = FakeApi(messages=[FakeMessage()])
        self.space.personal_api = FakeApi(messages=[FakeMessage()])

        self.assertEqual(self.space._last_message_id, 0)
        self.space.pull()
        self.assertEqual(self.context.get('puller.counter'), 1)
        self.assertTrue(self.space.api.messages.list.called)
        self.assertEqual(self.space._last_message_id, '*id')

        self.space.pull()
        self.assertEqual(self.context.get('puller.counter'), 2)
        self.assertEqual(self.space._last_message_id, '*id')

        self.space.pull()
        self.assertEqual(self.context.get('puller.counter'), 3)
        self.assertEqual(self.space._last_message_id, '*id')

        self.assertEqual(yaml.safe_load(self.ears.get()),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'pull',
                          'channel_id': None,
                          'type': 'message',
                          'is_direct': False,
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_on_message(self):

        logging.info("*** on_message")

        self.space.on_message(my_message, self.ears)
        message = my_message.copy()
        message.update({"type": "message"})
        message.update({"content": message['text']})
        message.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY'})
        message.update({"from_label": 'matt@example.com'})
        message.update({'is_direct': False})
        message.update({"mentioned_ids": ['Y2lzY29zcGFyazovL3VzL1BFT1BMRS8yNDlmNzRkOS1kYjhhLTQzY2EtODk2Yi04NzllZDI0MGFjNTM',
                       'Y2lzY29zcGFyazovL3VzL1BFT1BMRS83YWYyZjcyYy0xZDk1LTQxZjAtYTcxNi00MjlmZmNmYmM0ZDg']})
        message.update({"channel_id": 'Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), message)

        attachment = my_message.copy()
        attachment.update({"type": "attachment"})
        attachment.update({"url": "http://www.example.com/images/media.png"})
        attachment.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9mNWIzNjE4Ny1jOGRkLTQ3MjctOGIyZi1mOWM0NDdmMjkwNDY'})
        attachment.update({"from_label": 'matt@example.com'})
        attachment.update({"channel_id": 'Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIxYWQtNDNmMS0zYjU4LTkxNDctZjE0YmIwYzRkMTU0'})
        self.assertEqual(yaml.safe_load(self.ears.get()), attachment)

        self.space.on_message(my_private_message, self.ears)
        message = my_private_message.copy()
        message.update({"type": "message"})
        message.update({"content": message['text']})
        message.update({"from_id": 'Y2lzY29zcGFyazovL3VzL1LTQ5YzQtYTIyYi1mYWYwZWQwMjkyMzU'})
        message.update({"from_label": 'foo.bar@again.org'})
        message.update({'is_direct': True})
        message.update({"mentioned_ids": []})
        message.update({"channel_id": 'Y2lzY29zcGFyazovL3VzL1JP0zY2VmLWJiNDctOTZlZjA1NmJhYzFl'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), message)

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

        self.space.personal_token = '*void'
        self.space.token = None
        response = MyResponse(headers={'Content-Disposition': 'who cares'})
        self.assertEqual(self.space.name_attachment(url='/dummy', response=response),
                         'downloadable')

        self.space.personal_token = None
        self.space.token = '*void'
        response = MyResponse(headers={'Content-Disposition': 'filename="some_file.pdf"'})
        self.assertEqual(self.space.name_attachment(url='/dummy', response=response),
                         'some_file.pdf')

        self.space.personal_token = None
        self.space.token = None
        response = MyResponse(status_code=400, headers={'Content-Disposition': 'filename="some_file.pdf"'})
        with self.assertRaises(Exception):
            name = self.space.name_attachment(url='/dummy', response=response)

    def test_get_attachment(self):

        logging.info("*** get_attachment")

        class MyResponse(object):
            def __init__(self, status_code=200, headers={}):
                self.status_code = status_code
                self.headers = headers
                self.encoding = 'encoding'
                self.content = 'content'

        self.space.personal_token = '*void'
        self.space.token = None
        response = MyResponse(headers={})
        self.assertEqual(self.space.get_attachment(url='/dummy', response=response),
                         'content')

        self.space.personal_token = None
        self.space.token = '*void'
        response = MyResponse(headers={})
        self.assertEqual(self.space.get_attachment(url='/dummy', response=response),
                         'content')

        self.space.personal_token = None
        self.space.token = None
        response = MyResponse(status_code=400, headers={})
        with self.assertRaises(Exception):
            name = self.space.get_attachment(url='/dummy', response=response)

    def test_on_join(self):

        logging.info("*** on_join")

        self.space.on_join(my_join, self.ears)
        item = my_join.copy()
        item.update({"type": "join"})
        item.update({"actor_id": 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U'})
        item.update({"actor_address": 'foo.bar@acme.com'})
        item.update({"actor_label": 'Foo Bar'})
        item.update({"channel_id": 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), item)

    def test_on_leave(self):

        logging.info("*** on_leave")

        self.space.on_leave(my_leave, self.ears)
        item = my_leave.copy()
        item.update({"type": "leave"})
        item.update({"actor_id": 'Y2lzY29zcGFyazovL3VRiMTAtODZkYy02YzU0Yjg5ODA5N2U'})
        item.update({"actor_address": 'foo.bar@acme.com'})
        item.update({"actor_label": 'Foo Bar'})
        item.update({"channel_id": 'Y2lzY29zcGFyazovL3VzL1JP3LTk5MDAtMDU5MDI2YjBiNDUz'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), item)

    def test__to_channel(self):

        logging.info("*** _to_channel")

        channel = self.space._to_channel(FakeRoom())
        self.assertEqual(channel.id, '*id')
        self.assertEqual(channel.title, '*title')
        self.assertFalse(channel.is_direct)
        self.assertTrue(channel.is_group)
        self.assertFalse(channel.is_team)
        self.assertTrue(channel.is_moderated)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
