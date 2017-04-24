#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
import os
from multiprocessing import Process
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.spaces import SparkSpace


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


class FakeApi(object):

    def __init__(self, rooms=[], teams=[], messages=[]):

        self.rooms = Fake()
        self.rooms.list = mock.Mock(return_value=rooms)
        self.rooms.create = mock.Mock(return_value=FakeRoom())
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

        self.webhooks = Fake()
        self.webhooks.create = mock.Mock()

        self.people = Fake()
        self.people.me = mock.Mock()


class SparkSpaceTests(unittest.TestCase):

    def test_init(self):

        logging.debug("*** init")

        space = SparkSpace(ex_token='b', ex_ears='c')
        self.assertTrue(space.context is not None)
        self.assertEqual(space.token, 'b')
        self.assertEqual(space.ears, 'c')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, '*unknown*')
        self.assertEqual(space.teamId, None)

    def test_is_ready(self):

        logging.debug("*** is_ready")

        space = SparkSpace()
        self.assertFalse(space.is_ready)

        space = SparkSpace(context=Context({'spark.id': '123'}))
        self.assertTrue(space.is_ready)

    def test_configure(self):

        logging.debug("*** configure")

        space = SparkSpace(context=Context())
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
        self.assertEqual(space.context.get('spark.room'), 'My preferred room')
        self.assertEqual(space.context.get('spark.moderators'),
            ['foo.bar@acme.com', 'joe.bar@corporation.com'])
        self.assertEqual(space.context.get('spark.participants'),
            ['alan.droit@azerty.org', 'bob.nard@support.tv'])
        self.assertEqual(space.context.get('spark.team'), 'Anchor team')

        space = SparkSpace(context=Context())
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
            space = SparkSpace(context=Context())
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

            logging.debug("*** (life cycle)")

            space = SparkSpace(ex_token=cisco_spark_bearer)
            space.connect()
            space.bond(title='*transient*for*test')
            self.assertTrue(len(space.id) > 10)
            self.assertEqual(space.title, '*transient*for*test')
            self.assertEqual(space.teamId, None)

            space.post_message('Hello World')

            space.dispose()
            self.assertEqual(space.id, None)
            self.assertEqual(space.title, '*unknown*')
            self.assertEqual(space.team_id, None)

    def test_bond_mock(self):

        logging.debug("*** bond")

        space = SparkSpace()
        space.api = FakeApi()
        space.add_moderator = mock.Mock()
        space.add_participant = mock.Mock()

        space.bond(title='*title',
                   moderators=['who', 'knows'],
                   participants=['not', 'me'])

        self.assertTrue(space.add_moderator.called)
        self.assertTrue(space.add_participant.called)

    def test_lookup_space_mock(self):

        logging.debug("*** lookup_space")

        space = SparkSpace()
        space.api = FakeApi()

        flag = space.lookup_space(title='*does*not*exist*in*this*world')

        self.assertFalse(flag)
        self.assertTrue(space.api.rooms.list.called)

    def test_lookup_space_api(self):

        if cisco_spark_bearer is not None:

            logging.debug("*** lookup_space API")

            space = SparkSpace(ex_token=cisco_spark_bearer)
            space.connect()

            flag = space.lookup_space(title='*does*not*exist*in*this*world')

            self.assertFalse(flag)

    def test_create_space_mock(self):

        logging.debug("*** create_space")

        space = SparkSpace()
        space.api = FakeApi()
        space.create_space(title='*title')
        self.assertTrue(space.api.rooms.create.called)
        self.assertEqual(space.id, '*id')

    def test_add_moderators_mock(self):

        logging.debug("*** add_moderators")

        space = SparkSpace()
        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator_mock(self):

        logging.debug("*** add_moderator")

        space = SparkSpace()
        space.api = FakeApi()

        space.add_moderator(person='foo.bar@acme.com')

        self.assertTrue(space.api.memberships.create.called)

    def test_add_participants_mock(self):

        logging.debug("*** add_participants")

        space = SparkSpace()
        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant_mock(self):

        logging.debug("*** add_participant")
        space = SparkSpace()
        space.api = FakeApi()

        space.add_participant(person='foo.bar@acme.com')

        self.assertTrue(space.api.memberships.create.called)

    def test_dispose_mock(self):

        logging.debug("*** dispose")
        space = SparkSpace()
        space.api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')

        space.dispose()

        self.assertTrue(space.api.rooms.delete.called)

    def test_post_message_mock(self):

        logging.debug("*** post_message")
        space = SparkSpace()

        space.api = FakeApi()
        space.post_message(text='hello world')
        self.assertTrue(space.api.messages.create.called)

        space.api = FakeApi()
        space.post_message(ex_markdown='hello world')
        self.assertTrue(space.api.messages.create.called)

        try:
            space.api = FakeApi()
            space.post_message(text='hello world',
                               ex_markdown='hello world',
                               ex_file_path='./test_messages/sample.png')
            self.assertTrue(space.api.messages.create.called)
        except IOError:
            pass

    def test_register_mock(self):

        logging.debug("*** register")
        space = SparkSpace()

        space.api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')
        space.register('*hook')
        self.assertTrue(space.api.webhooks.create.called)

    def test_work(self):

        logging.debug("*** work")
        context = Context()
        space = SparkSpace(context=context)
        space.api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')

        mocked = mock.Mock(return_value=[])
        space.pull = mocked

        p = Process(target=space.work)
        p.daemon = True
        p.start()

        p.join(1.5)
        if p.is_alive():
            logging.info('Stopping puller')
            context.set('general.switch', 'off')
            p.join()

        self.assertFalse(p.is_alive())

    def test_pull_mock(self):

        logging.debug("*** pull")
        context = Context()
        space = SparkSpace(context=context)
        space.api = FakeApi(rooms=[FakeRoom()])
        space.bond(title='*title')
        space.pull()
        self.assertEqual(context.get('puller.counter'), 1)
        self.assertTrue(space.api.messages.list.called)

    def test_get_bot_mock(self):

        logging.debug("*** get_bot")
        space = SparkSpace()
        space.api = FakeApi()
        space.get_bot()
        self.assertTrue(space.api.people.me.called)

    def test_get_bot_api(self):

        if cisco_spark_bearer is not None:

            logging.debug("*** get_bot API")

            space = SparkSpace(bearer=cisco_spark_bearer)
            space.connect()
            item = space.get_bot()
            self.assertTrue(len(item.id) > 20)

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
