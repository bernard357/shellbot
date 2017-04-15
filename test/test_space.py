#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorlog
import unittest
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
import vcr

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, SparkSpace

class FakeRoom(object):
    id = '*id'
    title = '*title'
    teamId = None


class SpaceTests(unittest.TestCase):

    def test_init(self):

        logging.debug("*** Init")
        space = SparkSpace(context=Context(), bearer='b', ears='c')
        self.assertEqual(space.bearer, 'b')
        self.assertEqual(space.ears, 'c')
        self.assertEqual(space.room_id, None)
        self.assertEqual(space.room_title, '*unknown*')
        self.assertEqual(space.team_id, None)

    def test_configure(self):

        logging.debug("*** Configure")

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

        with self.assertRaises(KeyError): # missing key
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

#    @vcr.use_cassette(
#        os.path.abspath(os.path.dirname(__file__))+'/local/space_lifecycle.yaml')
    def test_lifecycle(self):

        logging.debug("*** life cycle")
        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)
        space.bond(space='*transient*for*test')
        self.assertTrue(len(space.room_id) > 10)
        self.assertEqual(space.room_title, '*transient*for*test')
        self.assertEqual(space.team_id, None)

        space.post_message('Hello World')

        space.dispose()
        self.assertEqual(space.room_id, None)
        self.assertEqual(space.room_title, '*unknown*')
        self.assertEqual(space.team_id, None)

    def test_bond_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[])
        space.api.rooms.create = mock.Mock(return_value=FakeRoom())
        space.add_moderator = mock.Mock()
        space.add_participant = mock.Mock()
        mocked = mock.Mock()
        space.bond(space='*space',
                   moderators=['who', 'knows'],
                   participants=['not', 'me'],
                   hook=mocked)
        self.assertTrue(space.add_moderator.called)
        self.assertTrue(space.add_participant.called)
        self.assertTrue(mocked.called)

    def test_get_space_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[FakeRoom()])
        item = space.get_space(space='*title')
        self.assertEqual(item.id, '*id')

        space.api.rooms.list = mock.Mock(return_value=[])
        space.api.rooms.create= mock.Mock(return_value=FakeRoom())
        item = space.get_space(space='*title')
        self.assertEqual(item.id, '*id')

    def test_lookup_space_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)
        mocked = mock.Mock(return_value=[FakeRoom()])
        space.api.rooms.list = mocked
        item = space.lookup_space('*space*does*not*exist*in*this*world')
        self.assertTrue(item is None)
        self.assertTrue(mocked.called)

#    @vcr.use_cassette(
#        os.path.abspath(os.path.dirname(__file__))+'/local/lookup_space.yaml')
    def test_lookup_space_api(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)
        item = space.lookup_space(space='*space*does*not*exist*in*this*world')
        self.assertEqual(item, None)

    def test_get_team_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)
        mocked = mock.Mock()
        space.api.teams.create = mocked
        item = space.get_team(team='*team*does*not*exist*in*this*world')
        self.assertTrue(mocked.called)

    def test_add_moderators_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)
        mocked = mock.Mock()
        space.api.memberships.create = mocked
        space.add_moderator(person='foo.bar@acme.com')
        self.assertTrue(mocked.called)

    def test_add_participants_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        mocked = mock.Mock()
        space.api.memberships.create = mocked
        space.add_participant(person='foo.bar@acme.com')
        self.assertTrue(mocked.called)

    def test_dispose_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[FakeRoom()])
        space.bond(space='*title')

        mocked = mock.Mock()
        space.api.rooms.delete = mocked
        space.dispose()
        self.assertTrue(mocked.called)

    def test_post_message_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        mocked = mock.Mock()
        space.api.messages.create = mocked
        space.post_message(text='hello world')
        self.assertTrue(mocked.called)

        mocked = mock.Mock()
        space.api.messages.create = mocked
        space.post_message(markdown='hello world')
        self.assertTrue(mocked.called)

        try:
            mocked = mock.Mock()
            space.api.messages.create = mocked
            space.post_message(text='hello world',
                               markdown='hello world',
                               file_path='./test_messages/sample.png')
            self.assertTrue(mocked.called)
        except IOError:
            pass

    def test_hook_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[FakeRoom()])
        space.bond(space='*title')

        mocked = mock.Mock()
        space.api.webhooks.create = mocked
        space.hook('*hook')
        self.assertTrue(mocked.called)

    def test_register_hook_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[FakeRoom()])
        space.bond(space='*title')

        mocked = mock.Mock()
        space.api.webhooks.create = mocked
        space.register_hook('*hook')
        self.assertTrue(mocked.called)

    def test_pull_for_ever_mock(self):

        context = Context()
        space = SparkSpace(context=context, bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[FakeRoom()])
        space.bond(space='*title')

        mocked = mock.Mock(return_value=[])
        space.pull = mocked

        p = Process(target=space.pull_for_ever)
        p.daemon = True
        p.start()

        p.join(1.5)
        if p.is_alive():
            logging.info('Stopping puller')
            context.set('general.switch', 'off')
            p.join()

        self.assertFalse(p.is_alive())

    def test_pull_mock(self):

        context = Context()
        space = SparkSpace(context=context, bearer=cisco_spark_bearer)

        space.api.rooms.list = mock.Mock(return_value=[FakeRoom()])
        space.bond(space='*title')

        mocked = mock.Mock(return_value=[])
        space.api.messages.list = mocked
        space.pull()
        self.assertEqual(context.get('puller.counter'), 1)

    def test_get_bot_mock(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)

        mocked = mock.Mock()
        space.api.people.me = mocked
        space.get_bot()
        self.assertTrue(mocked.called)

#    @vcr.use_cassette(
#        os.path.abspath(os.path.dirname(__file__))+'/local/get_bot.yaml')
    def test_get_bot_api(self):

        space = SparkSpace(context=Context(), bearer=cisco_spark_bearer)
        item = space.get_bot()
        self.assertTrue(len(item.id) > 20)

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

    cisco_spark_bearer = os.environ.get('CISCO_SPARK_BOT_TOKEN')
    if cisco_spark_bearer:
        sys.exit(unittest.main())
