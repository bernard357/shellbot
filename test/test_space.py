#!/usr/bin/env python

import colorlog
import unittest
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
import vcr

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.space import SparkSpace


cisco_spark_bearer = os.environ.get('CISCO_SPARK_BEARER')

class Response(object):
    def __init__(self, status=200):
        self.status_code = status

class EmptyListResponse(object):
    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
          "items" : []
        }

class MatchingSpaceListResponse(object):
    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
          "items" : [ {
            "id" : "*id",
            "title" : "*space",
            "type" : "group",
            "isLocked" : "false",
            "teamId" : "*teamId",
            "lastActivity" : "2016-04-21T19:12:48.920Z",
            "created" : "2016-04-21T19:01:55.966Z"
          } ]
        }



class SpaceTests(unittest.TestCase):

    def test_init(self):

        space = SparkSpace(context='a', bearer='b', ears='c')
        self.assertEqual(space.context, 'a')
        self.assertEqual(space.bearer, 'b')
        self.assertEqual(space.ears, 'c')
        self.assertEqual(space.room_id, None)
        self.assertEqual(space.room_title, '*unknown*')
        self.assertEqual(space.team_id, None)

    @vcr.use_cassette(
        os.path.abspath(os.path.dirname(__file__))+'/fixtures/space_lifecycle.yaml')
    def test_lifecycle(self):

        if cisco_spark_bearer:
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

    def test_reset(self):
        pass

    def test_bond_mock(self):

        context=Context()
        space = SparkSpace(context=context)

        responses_get = [
            Response(400),
            MatchingSpaceListResponse(),
            MatchingSpaceListResponse(),
            MatchingSpaceListResponse(),
        ]

        with mock.patch('requests.get',
                        side_effect=responses_get) as mocked_g:

            # http error code in List Rooms
            with self.assertRaises(Exception):
                space.bond(space='*space')

            # space already exists
            space.bond(space='*space')
            self.assertEqual(space.room_id, '*id')
            self.assertEqual(space.room_title, '*space')
            self.assertEqual(space.team_id, '*teamId')

            # add some people
            space.add_moderator = mock.Mock()
            space.add_participant = mock.Mock()
            space.bond(space='*space',
                       moderators=['who', 'knows'],
                       participants=['not', 'me'])
            self.assertTrue(space.add_moderator.called)
            self.assertTrue(space.add_participant.called)

            # add final hook
            mocked = mock.Mock()
            space.bond(space='*space', hook=mocked)
            self.assertTrue(mocked.called)
            mocked.assert_called_with('*id')

    def test_get_space_mock(self):

        context=Context()
        space = SparkSpace(context=context)

        class CreateSpaceResponse(object):
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                  "id" : "*id",
                  "title" : "*space",
                  "type" : "group",
                  "isLocked" : "false",
                  "teamId" : "*teamId",
                  "lastActivity" : "2016-04-21T19:12:48.920Z",
                  "created" : "2016-04-21T19:01:55.966Z"
                }

        responses_get = [
            Response(400),
            MatchingSpaceListResponse(),
            EmptyListResponse(),
            EmptyListResponse(),
        ]

        responses_post = [
            Response(400),
            CreateSpaceResponse(),
        ]

        with mock.patch('requests.get',
                        side_effect=responses_get) as mocked_g:

            with mock.patch('requests.post',
                            side_effect=responses_post) as mocked_p:

                # http error code in List Rooms
                #
                with self.assertRaises(Exception):
                    space.get_space('*space')

                # space already exists
                #
                item = space.get_space('*space')
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['title'], '*space')

                # http error code in Create Room
                #
                with self.assertRaises(Exception):
                    space.get_space('*space')

                # successful creation after lookup
                #
                item = space.get_space('*space')
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['title'], '*space')

        responses_get = [
            Response(400),
            MatchingSpaceListResponse(),
            MatchingSpaceListResponse(),
            EmptyListResponse(),
            EmptyListResponse(),
        ]

        responses_post = [
            CreateSpaceResponse(),
            CreateSpaceResponse(),
        ]

        teamOk = {
          "id" : "*teamId",
          "name" : "Another Fake",
          "created" : "2015-10-18T14:26:16+00:00"
        }

        teamBad = {
          "id" : "*team*is*not*good",
          "name" : "Another Fake",
          "created" : "2015-10-18T14:26:16+00:00"
        }

        with mock.patch('requests.get',
                        side_effect=responses_get) as mocked_g:

            with mock.patch('requests.post',
                            side_effect=responses_post) as mocked_p:

                # http error code on List Rooms
                with self.assertRaises(Exception):
                    space.get_space('*space', teamOk)

                # matching room, but unexpected team id
                # should generate a warning only
                item = space.get_space('*space', teamBad)
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['title'], '*space')

                # matching room and expected team
                item = space.get_space('*space', teamOk)
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['title'], '*space')

                # new room has unexpected team id
                # should only generate a warning
                item = space.get_space('*space', teamBad)
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['title'], '*space')

                # new room has expected team id
                item = space.get_space('*space', teamOk)
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['title'], '*space')

    @vcr.use_cassette(
        os.path.abspath(os.path.dirname(__file__))+'/fixtures/get_space.yaml')
    def test_get_space_api(self):

        context=Context()

        space = SparkSpace(context=context, bearer='*dummy')
        with self.assertRaises(Exception):
            space.get_space('*do*not*exist')

    def test_lookup_space_mock(self):

        context=Context()
        space = SparkSpace(context=context)

        class NoMatchingSpaceListResponse(object):
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                  "items" : [ {
                    "id" : "*id",
                    "title" : "*space*do*not*match",
                    "type" : "group",
                    "isLocked" : "false",
                    "teamId" : "*teamId",
                    "lastActivity" : "2016-04-21T19:12:48.920Z",
                    "created" : "2016-04-21T19:01:55.966Z"
                  } ]
                }

        responses_get = [
            Response(400),
            MatchingSpaceListResponse(),
            NoMatchingSpaceListResponse(),
            EmptyListResponse(),
        ]

        with mock.patch('requests.get',
                        side_effect=responses_get) as mocked_g:

            # http error code in List Rooms
            #
            with self.assertRaises(Exception):
                space.lookup_space('*space')

            # space already exists
            #
            item = space.lookup_space('*space')
            self.assertEqual(item['id'], '*id')
            self.assertEqual(item['title'], '*space')

            # space does not exist
            #
            item = space.lookup_space('*space')
            self.assertEqual(item, None)

            # no space at all
            #
            item = space.lookup_space('*space')
            self.assertEqual(item, None)

    @vcr.use_cassette(
        os.path.abspath(os.path.dirname(__file__))+'/fixtures/lookup_space.yaml')
    def test_lookup_space_api(self):

        context=Context()

        space = SparkSpace(context=context, bearer='*dummy')
        with self.assertRaises(Exception):
            space.lookup_space('*do*not*exist')

        if cisco_spark_bearer:
            space = SparkSpace(context=context, bearer=cisco_spark_bearer)
            item = space.lookup_space('*do*not*exist')
            self.assertEqual(item, None)

    def test_get_team_mock(self):

        context=Context()
        space = SparkSpace(context=context)
        space.room_id = '*roomId'

        class MatchingTeamListResponse(object):
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                  "items" : [ {
                    "id" : "*id",
                    "name" : "*test",
                    "created" : "2015-10-18T14:26:16+00:00"
                  } ]
                }

        class CreateTeamResponse(object):
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                    "id" : "*id",
                    "name" : "*test",
                    "created" : "2015-10-18T14:26:16+00:00"
                }

        responses_get = [
            Response(400),
            MatchingTeamListResponse(),
            EmptyListResponse(),
            EmptyListResponse(),
        ]

        responses_post = [
            Response(400),
            CreateTeamResponse(),
        ]

        with mock.patch('requests.get',
                        side_effect=responses_get) as mocked_g:

            with mock.patch('requests.post',
                            side_effect=responses_post) as mocked_p:

                # http error on List Teams
                with self.assertRaises(Exception):
                    space.get_team('*test')

                # team exists
                item = space.get_team('*test')
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['name'], '*test')

                # http error on Create Team
                with self.assertRaises(Exception):
                    space.get_team('*test')

                # team has been successfully created
                item = space.get_team('*test')
                self.assertEqual(item['id'], '*id')
                self.assertEqual(item['name'], '*test')

    def test_add_moderators_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch('requests.post',
                        return_value=Response(200)) as mocked:

            space.add_moderator(person='foo.bar@acme.com')
            mocked.assert_called_with(
                data={'isModerator': 'true',
                      'roomId': None,
                      'personEmail': 'foo.bar@acme.com'},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/memberships')

        with mock.patch('requests.post',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.add_moderator(person='foo.bar@acme.com')

    def test_add_participants_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch('requests.post',
                        return_value=Response(200)) as mocked:

            space.add_participant(person='foo.bar@acme.com')
            mocked.assert_called_with(
                data={'isModerator': 'false',
                      'roomId': None,
                      'personEmail': 'foo.bar@acme.com'},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/memberships')

        with mock.patch('requests.post',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.add_participant(person='foo.bar@acme.com')

    def test_dispose_mock(self):

        space = SparkSpace(context='a', bearer='b', ears='c')

        with mock.patch('requests.get',
                        return_value=EmptyListResponse()) as mocked:

            space.dispose('*unknown*space*')
            mocked.assert_called_with(
                headers={'Authorization': 'Bearer b'},
                url='https://api.ciscospark.com/v1/rooms')

        with mock.patch('requests.get',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.dispose('*unknown*space*')

    def test_build_message(self):

        space = SparkSpace(context=None)

        message = space.build_message()
        expected = {'text': ''}
        self.assertEqual(message, expected)

        message = space.build_message(text='hello world')
        expected = {'text': 'hello world'}
        self.assertEqual(message, expected)

        message = space.build_message(text=['hello', 'world'])
        expected = {'text': 'hello\nworld'}
        self.assertEqual(message, expected)

        message = space.build_message(markdown='this is a **bold** statement')
        expected = {'markdown': 'this is a **bold** statement'}
        self.assertEqual(message, expected)

        message = space.build_message(markdown=['* line 1', '* line 2'])
        expected = {'markdown': '* line 1\n* line 2'}
        self.assertEqual(message, expected)

        message = space.build_message(
            text='hello world',
            markdown='this is a **bold** statement')
        expected = {
            'text': 'hello world',
            'markdown': 'this is a **bold** statement'}
        self.assertEqual(message, expected)

        try:
            message = space.build_message(
                file_path='./test_messages/sample.png',
                file_label='pres')
            self.assertEqual(message['files'][0], 'pres')
            self.assertEqual(message['files'][2], 'application/octet-stream')
            self.assertEqual(message['text'], 'pres')
        except IOError:
            pass

        try:
            message = space.build_message(
                text='hello world',
                file_path='./test_messages/sample.png',
                file_label='pres')
            self.assertEqual(message['files'][0], 'pres')
            self.assertEqual(message['files'][2], 'application/octet-stream')
            self.assertEqual(message['text'], 'hello world')
        except IOError:
            pass

        try:
            message = space.build_message(
                markdown='this is a **bold** statement',
                file_path='./test_messages/sample.png',
                file_label='pres')
            self.assertEqual(message['files'][0], 'pres')
            self.assertEqual(message['files'][2], 'application/octet-stream')
            self.assertEqual(message['text'], 'pres')
            self.assertEqual(message['markdown'],
                             'this is a **bold** statement')
        except IOError:
            pass

        try:
            message = space.build_message(
                text='hello world',
                markdown='this is a **bold** statement',
                file_path='./test_messages/sample.png',
                file_label='pres')
            self.assertEqual(message['files'][0], 'pres')
            self.assertEqual(message['files'][2], 'application/octet-stream')
            self.assertEqual(message['text'], 'hello world')
            self.assertEqual(message['markdown'],
                             'this is a **bold** statement')
        except IOError:
            pass

    def test_post_message_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch('requests.post',
                        return_value=Response(200)) as mocked:

            space.post_message('hello world')
            mocked.assert_called_with(
                data={'text': 'hello world', 'roomId': None},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/messages')

            message = space.build_message(text='hello world')
            space.post_message(message)

            try:
                message = space.build_message(
                    text='hello world',
                    markdown='this is a **bold** statement',
                    file_path='./test_messages/sample.png',
                    file_label='pres')
                space.post_message(message)

            except IOError:
                pass

        with mock.patch('requests.post',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.post_message('hello world')

            message = space.build_message(text='hello world')
            with self.assertRaises(Exception):
                space.post_message(message)

            try:
                message = space.build_message(
                    text='hello world',
                    markdown='this is a **bold** statement',
                    file_path='./test_messages/sample.png',
                    file_label='pres')
                with self.assertRaises(Exception):
                    space.post_message(message)

            except IOError:
                pass

    def test_connect_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')
        space.room_id = '*roomId'

        with mock.patch('requests.post',
                        return_value=Response(200)) as mocked:

            space.connect('*hook')
            mocked.assert_called_with(
                data={'filter': 'roomId=*roomId',
                      'targetUrl': '*hook',
                      'resource': 'messages',
                      'name': 'controller-webhook',
                      'event': 'created'},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/webhooks')

        with mock.patch('requests.post',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.connect('*hook')

    def test_register_hook_mock(self):

        space = SparkSpace(context=None, bearer='*dummy')
        space.room_id = '*roomId'

        with mock.patch('requests.post',
                        return_value=Response(200)) as mocked:

            space.register_hook('*hook')
            mocked.assert_called_with(
                data={'filter': 'roomId=*roomId',
                      'targetUrl': '*hook',
                      'resource': 'messages',
                      'name': 'controller-webhook',
                      'event': 'created'},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/webhooks')

        with mock.patch('requests.post',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.register_hook('*hook')

    def test_pull_for_ever_mock(self):

        context=Context()
        space = SparkSpace(context=context, bearer='*dummy')
        space.room_id = '*roomId'

        with mock.patch('requests.get',
                        return_value=EmptyListResponse()) as mocked:

            p = Process(target=space.pull_for_ever)
            p.daemon = True
            p.start()

            p.join(1.5)
            if p.is_alive():
                logging.info('Stopping puller')
                context.set('general.switch', 'off')
                p.join()

            self.assertFalse(p.is_alive())
            self.assertEqual(context.get('puller.counter'), 2)

    def test_pull_mock(self):

        context=Context()
        space = SparkSpace(context=context, bearer='*dummy')
        space.room_id = '*roomId'

        with mock.patch('requests.get',
                        return_value=EmptyListResponse()) as mocked:

            space.pull()
            mocked.assert_called_with(
                headers={'Authorization': 'Bearer *dummy'},
                params={'max': 10, 'roomId': '*roomId'},
                url='https://api.ciscospark.com/v1/messages')

        with mock.patch('requests.get',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.pull()

        with mock.patch('requests.get',
                        return_value=Response(403)) as mocked:

            space.pull()

    def test_get_bot_mock(self):

        context=Context()
        space = SparkSpace(context=context, bearer='*dummy')
        space.room_id = '*roomId'

        class BotResponse(object):
            def __init__(self, status=200):
                self.status_code = status

            def json(self):
                return {'id': '*dummy_id'}

        with mock.patch('requests.get',
                        return_value=BotResponse()) as mocked:

            item = space.get_bot()
            mocked.assert_called_with(
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/people/me')
            self.assertEqual(item['id'], '*dummy_id')

        with mock.patch('requests.get',
                        return_value=Response(401)) as mocked:

            with self.assertRaises(Exception):
                space.get_bot()

    @vcr.use_cassette(
        os.path.abspath(os.path.dirname(__file__))+'/fixtures/get_bot.yaml')
    def test_get_bot_api(self):

        context=Context()

        space = SparkSpace(context=context, bearer='*dummy')
        with self.assertRaises(Exception):
            space.get_bot()

        if cisco_spark_bearer:
            space = SparkSpace(context=context, bearer=cisco_spark_bearer)
            item = space.get_bot()
            self.assertTrue(len(item['id']) > 20)

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
