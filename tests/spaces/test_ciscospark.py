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
from shellbot.events import Event, Message, Join, Leave
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
    isLocked = False
    title = '*team_title'
    type = 'team'
    teamId = None


class FakeChannel(object):
    id = '*123'
    title = '*title'
    is_direct = False
    is_moderated = False


class FakeMessage(Fake):
    id = '*123'
    message = '*message'
    _json = {'text': '*message', 'created': "2017-07-19T05:29:23.962Z"}


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
                 message=FakeMessage(),
                 persons=[],
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
        self.memberships.list = mock.Mock(return_value=persons)
        self.memberships.create = mock.Mock()
        self.memberships.delete = mock.Mock()

        self.messages = Fake()
        self.messages.list = mock.Mock(return_value=messages if messages else [message])
        self.messages.create = mock.Mock(return_value=message)
        self.messages.delete = mock.Mock()
        self.messages.get = mock.Mock(return_value=message)

        self.webhooks = Fake()
        self.webhooks.list = mock.Mock(return_value=[])
        self.webhooks.create = mock.Mock()

        self.people = Fake()
        self.people.me = mock.Mock(return_value=me)


my_message = {
    "id" : "1_lzY29zcGFyazovL3VzL01FU1NBR0UvMWU2LThhZTktZGQ1YjNkZmM1NjVk",
    "roomId" : "*id1",
    "roomType" : "group",
    "toPersonId" : "*julie*id",
    "toPersonEmail" : "julie@example.com",
    "text" : "The PM for this project is Mike C. and the Engineering Manager is Jane W.",
    "markdown" : "**PROJECT UPDATE** A new project plan has been published [on Box](http://box.com/s/lf5vj). The PM for this project is <@personEmail:mike@example.com> and the Engineering Manager is <@personEmail:jane@example.com>.",
    "files" : [ "http://www.example.com/images/media.png" ],
    "personId" : "*matt*id",
    "personEmail" : "matt@example.com",
    "created" : "2015-10-18T14:26:16+00:00",
    "hook": "shellbot-messages",
    "mentionedPeople" : [ "*matt*id", "*julie*id" ],
}

my_private_message = {
    "id": "Y2lzY29zcGFyazovL3VzL01FU1NB0xMWU3LTljODctNTljZjJjNDRhYmIy",
    "roomId": "*direct*id",
    "roomType": "direct",
    "text": "test",
    "created": "2017-07-22T16:49:22.008Z",
    "hook": "shellbot-messages",
    "personEmail": "foo.bar@again.org",
    "personId": "*foo*id",
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
        self.fan = Queue()
        self.space = SparkSpace(context=self.context,
                                ears=self.ears,
                                fan=self.fan)

    def tearDown(self):
        del self.space
        del self.fan
        del self.ears
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_on_init(self):

        logging.info("*** on_init")

        self.assertEqual(self.space.prefix, 'spark')
        self.assertEqual(self.space.get('token'), None)
        self.assertEqual(self.space.api, None)
        self.assertEqual(self.space._last_message_id, 0)

        space = SparkSpace(context=self.context, token='b')
        self.assertEqual(space.get('token'), 'b')

    def test_configure(self):

        logging.info("*** configure")

        settings={  # from settings to member attributes
            'spark': {
                'room': 'My preferred room',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
            }
        }
        self.space.configure(settings=settings)
        self.assertEqual(self.space.get('room'), 'My preferred room')
        self.assertEqual(self.space.configured_title(), 'My preferred room')
        self.assertEqual(self.space.get('participants'),
            ['alan.droit@azerty.org', 'bob.nard@support.tv'])
        self.assertEqual(self.space.get('token'), 'hkNWEtMJNkODVGlZWU1NmYtyY')

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
        with self.assertRaises(AssertionError):
            self.space.connect()

        self.space.set('token', 'a')
        self.space.connect(factory=my_factory)
        self.assertEqual(self.space.api.token, 'a')
        self.assertEqual(self.space.audit_api, None)

        self.space.set('token', 'a')
        self.space.set('audit_token', 'b')
        self.space.connect(factory=my_factory)
        self.assertEqual(self.space.api.token, 'a')
        self.assertEqual(self.space.audit_api.token, 'b')

    def test_on_connect(self):

        logging.info("*** on_connect")

        self.space.api = FakeApi(me=FakeBot())
        self.space.on_connect()
        self.assertTrue(self.space.api.people.me.called)
        self.assertEqual(self.context.get('bot.address'), 'shelly@sparkbot.io')
        self.assertEqual(self.context.get('bot.name'), 'shelly')
        self.assertTrue(len(self.context.get('bot.id')) > 20)

    def test_list_group_channels(self):

        logging.info("*** list_group_channels")

        self.space.api = FakeApi()
        channels = self.space.list_group_channels()
        self.assertEqual(len(channels), 1)
        self.assertTrue(self.space.api.rooms.list.called)
        channel = channels[0]
        self.assertEqual(channel.id, '*id')
        self.assertEqual(channel.title, '*title')

    def test_create(self):

        logging.info("*** create")

        with self.assertRaises(AssertionError):
            self.space.create(title=None)

        with self.assertRaises(AssertionError):
            self.space.create(title='')

        with self.assertRaises(AssertionError):
            self.space.create(title='*title')

        self.space.api = FakeApi()
        channel = self.space.create(title='*title')
        self.assertTrue(self.space.api.rooms.create.called)
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

        self.space.api = FakeApi()
        channel = self.space.get_by_title('*does*not*exist')
        self.assertEqual(channel, None)
        self.assertTrue(self.space.api.rooms.list.called)

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

        self.space.api.rooms = Intruder()
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

        self.space.api = FakeApi()

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

        self.space.api.rooms = Intruder()
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
        self.space.delete(id='*id')
        self.assertTrue(self.space.api.rooms.delete.called)

        # explicit id, room does not exists
        self.space.api = FakeApi()
        self.space.delete(id='*ghost*room')
        self.assertTrue(self.space.api.rooms.delete.called)

    def test_get_team(self):

        logging.info("*** get_team")

        class Team(object):
            name = '*name'
            id = '456'

        self.space.api = FakeApi(teams=[Team()])
        team = self.space.get_team(name='*name')
        self.assertTrue(self.space.api.teams.list.called)
        self.assertEqual(team.name, '*name')
        self.assertEqual(team.id, '456')

        self.space.api = FakeApi(teams=[Team()])
        team = self.space.get_team(name='*unknown')
        self.assertTrue(self.space.api.teams.list.called)
        self.assertEqual(team, None)

    def test_list_participants(self):

        logging.info("*** list_participants")

        self.space.api = FakeApi()
        self.space.list_participants(id='*id')
        self.assertTrue(self.space.api.memberships.list.called)

    def test_add_participants(self):

        logging.info("*** add_participants")

        with mock.patch.object(self.space,
                               'add_participant') as mocked:

            self.space.add_participants(id='*id', persons=['foo.bar@acme.com'])
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_add_participant(self):

        logging.info("*** add_participant")

        self.space.api = FakeApi()
        self.space.add_participant(id='*id', person='foo.bar@acme.com')
        self.assertTrue(self.space.api.memberships.create.called)

    def test_remove_participants(self):

        logging.info("*** remove_participants")

        with mock.patch.object(self.space,
                               'remove_participant') as mocked:

            self.space.remove_participants(id='*id', persons=['foo.bar@acme.com'])
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_remove_participant(self):

        logging.info("*** remove_participant")

        self.space.api = FakeApi()
        self.space.remove_participant(id='*id', person='foo.bar@acme.com')
        self.assertTrue(self.space.api.memberships.delete.called)

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

        self.context.set('bot.id', '*id')
        self.context.set('spark.token', '*token')

        self.space.api = FakeApi()
        self.space.register('*hook')
        self.assertTrue(self.space.api.webhooks.create.called)
        self.assertFalse(self.context.get('audit.has_been_armed'))

        self.space.api = FakeApi()
        self.space.audit_api = FakeApi()
        self.space.register('*hook')
        self.assertTrue(self.space.api.webhooks.create.called)
        self.assertTrue(self.context.get('audit.has_been_armed'))

    def test_deregister(self):

        logging.info("*** deregister")

        self.space.api = FakeApi()
        self.context.set('bot.id', '*id')
        self.space.deregister()
        self.assertTrue(self.space.api.webhooks.list.called)

    def test_run(self):

        logging.info("*** run")

        self.space.api = FakeApi()

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

        fake_message = {
            u'status': u'active',
            u'resource': u'messages',
            u'name': u'shellbot-messages',
            u'created': u'2017-07-30T20:14:24.050Z',
            u'appId': u'Y2lzY29zcGFyazovL3VzLmM3ZDUxNWNiNGEwY2M5MWFh',
            u'id': u'Y2lzY29zcGFyazovL3VzjI0MTM2ZjgwY2Yy',
            u'orgId': u'Y2lzY29zcGFyazovL3VYjU1ZS00ODYzY2NmNzIzZDU',
            u'createdBy': u'Y2lzY29zcGFyazovL3VzLS01ZGI5M2Y5MjI5MWM',
            u'targetUrl': u'http://0dab1.ngrok.io/hook',
            u'ownedBy': u'creator',
            u'actorId': u'Y2lzY29zcGFyazovL3VzL1BFkyMzU',
            u'data': {
                u'roomType': u'group',
                u'created': u'2017-07-30T20:14:50.882Z',
                u'personId': u'Y2lzY29zcGFyayYi1mYWYwZWQwMjkyMzU',
                u'personEmail': u'foo.bar@acme.com',
                u'mentionedPeople': [u'Y2lzY29zcGFyazovL3VGI5M2Y5MjI5MWM'],
                u'roomId': u'Y2lzY29zcGFyazovL3VzL1NzUtYzc2ZDMyOGY0Y2Rj',
                u'id': '*123',
                },
            u'event': u'created',
        }
        self.space.api = FakeApi()
        self.assertEqual(self.space.webhook(fake_message), 'OK')
        self.assertTrue(self.space.api.messages.get.called)
        data = self.space.ears.get()
        self.assertEqual(yaml.safe_load(data),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'shellbot-messages',
                          'stamp': '2017-07-19T05:29:23.962Z',
                          'created': '2017-07-19T05:29:23.962Z',
                          'channel_id': None,
                          'type': 'message',
                          'is_direct': False,
                          'mentioned_ids': []})

        with self.assertRaises(Exception):
            print(self.space.ears.get_nowait())
        with self.assertRaises(Exception):
            print(self.space.fan.get_nowait())

        fake_message = {
            u'status': u'active',
            u'resource': u'messages',
            u'name': u'shellbot-audit',
            u'created': u'2017-07-30T20:25:29.924Z',
            u'appId': u'Y2lzY29zcGFyazovL3VzL0FQUE2YyNjZhYmY2NmM5OTllYzFm',
            u'id': u'Y2lzY29zcGFyazovL3VzL1dFC00NzllLTg0MDQtZGQ2NGJiNTk3Nzdi',
            u'orgId': u'Y2lzY29zcGFyazovL3VzL09SR0FOSVpBVY2NmNzIzZDU',
            u'createdBy': u'Y2lzY29zcGFyazovL3VzL1BFTTIyYi1mYWYwZWQwMjkyMzU',
            u'targetUrl': u'http://0dab1.ngrok.io/hook',
            u'ownedBy': u'creator',
            u'actorId': u'Y2lzY29zcGFyazovL3VzLM2Y5MjI5MWM',
            u'data': {
                u'files': [u'http://hydra-a5.wbx2.com/contents/Y2lzY29zcGFWY5LzA'],
                u'roomType': u'group',
                u'created': u'2017-07-30T20:25:33.803Z',
                u'personId': u'Y2lzY29zcGFyazovL3VzL1BFT5M2Y5MjI5MWM',
                u'personEmail': u'shelly@sparkbot.io',
                u'roomId': u'Y2lzY29zcGFyazovL3VzL1JPTyNmFhNWYxYTY4',
                u'id': u'*123',
                },
            u'event': u'created',
        }

        self.space.audit_api = FakeApi()
        self.assertEqual(self.space.webhook(fake_message), 'OK')
        self.assertTrue(self.space.audit_api.messages.get.called)
        data = self.space.fan.get()
        self.assertEqual(yaml.safe_load(data),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'shellbot-audit',
                          'stamp': '2017-07-19T05:29:23.962Z',
                          'created': '2017-07-19T05:29:23.962Z',
                          'channel_id': None,
                          'type': 'message',
                          'is_direct': False,
                          'mentioned_ids': []})

        with self.assertRaises(Exception):
            print(self.space.ears.get_nowait())
        with self.assertRaises(Exception):
            print(self.space.fan.get_nowait())

    def test_pull(self):

        logging.info("*** pull")

        self.space.api = FakeApi(messages=[FakeMessage()])

        self.assertEqual(self.space._last_message_id, 0)
        self.space.pull()
        self.assertEqual(self.context.get('puller.counter'), 1)
        self.assertTrue(self.space.api.messages.list.called)
        self.assertEqual(self.space._last_message_id, '*123')

        self.space.pull()
        self.assertEqual(self.context.get('puller.counter'), 2)
        self.assertEqual(self.space._last_message_id, '*123')

        self.space.pull()
        self.assertEqual(self.context.get('puller.counter'), 3)
        self.assertEqual(self.space._last_message_id, '*123')

        self.assertEqual(yaml.safe_load(self.ears.get()),
                         {'text': '*message',
                          'content': '*message',
                          'from_id': None,
                          'from_label': None,
                          'hook': 'pull',
                          'stamp': '2017-07-19T05:29:23.962Z',
                          'created': '2017-07-19T05:29:23.962Z',
                          'channel_id': None,
                          'type': 'message',
                          'is_direct': False,
                          'mentioned_ids': []})
        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_on_message(self):

        logging.info("*** on_message")

        class MySpace(SparkSpace):
            def name_attachment(self, url, token=None):
                return 'some_file.pdf'

            def get_attachment(self, url, token=None):
                return b'hello world'

        self.space = MySpace(context=self.context)

        self.space.on_message(my_message, self.ears)
        message = my_message.copy()
        message.update({"type": "message"})
        message.update({"content": message['text']})
        message.update({"attachment": "some_file.pdf"})
        message.update({"url": "http://www.example.com/images/media.png"})
        message.update({"from_id": '*matt*id'})
        message.update({"from_label": 'matt@example.com'})
        message.update({'is_direct': False})
        message.update({"mentioned_ids": ['*matt*id', '*julie*id']})
        message.update({"channel_id": '*id1'})
        message.update({"stamp": '2015-10-18T14:26:16+00:00'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), message)

        self.space.on_message(my_private_message, self.ears)
        message = my_private_message.copy()
        message.update({"type": "message"})
        message.update({"content": message['text']})
        message.update({"from_id": '*foo*id'})
        message.update({"from_label": 'foo.bar@again.org'})
        message.update({'is_direct': True})
        message.update({"mentioned_ids": []})
        message.update({"channel_id": '*direct*id'})
        message.update({"stamp": '2017-07-22T16:49:22.008Z'})
        self.maxDiff = None
        self.assertEqual(yaml.safe_load(self.ears.get()), message)

        with self.assertRaises(Exception):
            print(self.ears.get_nowait())

    def test_download_attachment(self):

        logging.info("*** download_attachment")

        class MySpace(SparkSpace):
            def name_attachment(self, url, token=None):
                return 'some_file.pdf'

            def get_attachment(self, url, token=None):
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

        self.space.token = None
        response = MyResponse(headers={'Content-Disposition': 'who cares'})
        self.assertEqual(self.space.name_attachment(url='/dummy', response=response),
                         'downloadable')

        self.space.token = '*void'
        response = MyResponse(headers={'Content-Disposition': 'filename="some_file.pdf"'})
        self.assertEqual(self.space.name_attachment(url='/dummy', response=response),
                         'some_file.pdf')

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

        self.space.token = None
        response = MyResponse(headers={})
        self.assertEqual(self.space.get_attachment(url='/dummy', response=response),
                         'content')

        self.space.token = '*void'
        response = MyResponse(headers={})
        self.assertEqual(self.space.get_attachment(url='/dummy', response=response),
                         'content')

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
        item.update({"stamp": '2017-05-31T21:25:30.424Z'})
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
        item.update({"stamp": '2017-05-31T21:25:30.424Z'})
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

        channel = self.space._to_channel(FakeDirectRoom())
        self.assertEqual(channel.id, '*direct_id')
        self.assertEqual(channel.title, 'Marcel Jones')
        self.assertTrue(channel.is_direct)
        self.assertFalse(channel.is_group)
        self.assertFalse(channel.is_team)
        self.assertFalse(channel.is_moderated)

        channel = self.space._to_channel(FakeTeamRoom())
        self.assertEqual(channel.id, '*team_id')
        self.assertEqual(channel.title, '*team_title')
        self.assertFalse(channel.is_direct)
        self.assertTrue(channel.is_group)
        self.assertTrue(channel.is_team)
        self.assertFalse(channel.is_moderated)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
