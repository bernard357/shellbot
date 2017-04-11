#!/usr/bin/env python

import colorlog
import unittest
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.space import SparkSpace


class SpaceTests(unittest.TestCase):

    def test_init(self):

        space = SparkSpace(context='a', bearer='b', ears='c')
        self.assertEqual(space.context, 'a')
        self.assertEqual(space.bearer, 'b')
        self.assertEqual(space.ears, 'c')
        self.assertEqual(space.room_id, None)

        with self.assertRaises(Exception):
            space.dispose('*unknown*space*')

    def test_get_bot_id(self):

        context=Context()
        space = SparkSpace(context=context, bearer='*dummy')
        space.room_id = '*roomId'

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

            def json(self):
                return {'id': '*dummy_id'}

        response_200 = Response(200)
        response_401 = Response(401)

        with mock.patch('requests.get',
                        return_value=response_200) as mocked:

            space.get_bot_id()
            mocked.assert_called_with(
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/people/me')

        with mock.patch('requests.get',
                        return_value=response_401) as mocked:

            with self.assertRaises(Exception):
                space.get_bot_id()

    def test_add_moderators(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator(self):

        space = SparkSpace(context=None, bearer='*dummy')

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

        response_200 = Response(200)
        response_401 = Response(401)

        with mock.patch('requests.post',
                        return_value=response_200) as mocked:

            space.add_moderator(person='foo.bar@acme.com')
            mocked.assert_called_with(
                data={'isModerator': 'true',
                      'roomId': None,
                      'personEmail': 'foo.bar@acme.com'},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/memberships')

        with mock.patch('requests.post',
                        return_value=response_401) as mocked:

            with self.assertRaises(Exception):
                space.add_moderator(person='foo.bar@acme.com')

    def test_add_participants(self):

        space = SparkSpace(context=None, bearer='*dummy')

        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant(self):

        space = SparkSpace(context=None, bearer='*dummy')

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

        response_200 = Response(200)
        response_401 = Response(401)

        with mock.patch('requests.post',
                        return_value=response_200) as mocked:

            space.add_participant(person='foo.bar@acme.com')
            mocked.assert_called_with(
                data={'isModerator': 'false',
                      'roomId': None,
                      'personEmail': 'foo.bar@acme.com'},
                headers={'Authorization': 'Bearer *dummy'},
                url='https://api.ciscospark.com/v1/memberships')

        with mock.patch('requests.post',
                        return_value=response_401) as mocked:

            with self.assertRaises(Exception):
                space.add_participant(person='foo.bar@acme.com')

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

    def test_post_message(self):

        space = SparkSpace(context=None, bearer='*dummy')

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

        response_200 = Response(200)
        response_401 = Response(401)

        with mock.patch('requests.post',
                        return_value=response_200) as mocked:

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
                        return_value=response_401) as mocked:

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

    def test_connect(self):

        space = SparkSpace(context=None, bearer='*dummy')
        space.room_id = '*roomId'

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

        response_200 = Response(200)
        response_401 = Response(401)

        with mock.patch('requests.post',
                        return_value=response_200) as mocked:

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
                        return_value=response_401) as mocked:

            with self.assertRaises(Exception):
                space.connect('*hook')

    def test_register_hook(self):

        space = SparkSpace(context=None, bearer='*dummy')
        space.room_id = '*roomId'

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

        response_200 = Response(200)
        response_401 = Response(401)

        with mock.patch('requests.post',
                        return_value=response_200) as mocked:

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
                        return_value=response_401) as mocked:

            with self.assertRaises(Exception):
                space.register_hook('*hook')

    def test_pull_for_ever(self):

        context=Context()
        space = SparkSpace(context=context, bearer='*dummy')
        space.room_id = '*roomId'

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

            def json(self):
                return {'items': []}

        response_200 = Response(200)
        response_401 = Response(401)
        response_403 = Response(403)

        with mock.patch('requests.get',
                        return_value=response_200) as mocked:

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

    def test_pull(self):

        context=Context()
        space = SparkSpace(context=context, bearer='*dummy')
        space.room_id = '*roomId'

        class Response(object):
            def __init__(self, status=200):
                self.status_code = status

            def json(self):
                return {'items': []}

        response_200 = Response(200)
        response_401 = Response(401)
        response_403 = Response(403)

        with mock.patch('requests.get',
                        return_value=response_200) as mocked:

            space.pull()
            mocked.assert_called_with(
                headers={'Authorization': 'Bearer *dummy'},
                params={'max': 10, 'roomId': '*roomId'},
                url='https://api.ciscospark.com/v1/messages')

        with mock.patch('requests.get',
                        return_value=response_401) as mocked:

            with self.assertRaises(Exception):
                space.pull()

        with mock.patch('requests.get',
                        return_value=response_403) as mocked:

            space.pull()

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
