#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import json
import io
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
import time

from shellbot import Context
from shellbot.spaces import LocalSpace


def clear_env(name):
    try:
        os.environ.pop(name)
    except KeyError:
        pass


class FakeChannel(object):
    id = '*123'
    title = '*title'
    is_direct = False
    is_moderated = False


class LocalSpaceTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.context.set('bot.id', '*bot')
        self.ears = Queue()
        self.space = LocalSpace(context=self.context, ears=self.ears)

    def tearDown(self):
        del self.space
        del self.ears
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_on_init(self):

        logging.info("***** init")

        self.assertEqual(self.space.prefix, 'space')
        self.assertEqual(self.space.participants, [])
        self.assertEqual(self.space.input, [])

        space = LocalSpace(context=self.context, input='hello world')
        self.assertEqual(space.input, ['hello world'])

        space = LocalSpace(context=self.context, input=['hello', 'world'])
        self.assertEqual(space.input, ['hello', 'world'])

    def test_push(self):

        logging.info("***** push")

        self.space.push(input=None)
        self.assertEqual(self.space.input, [])

        self.space.push(input='')
        self.assertEqual(self.space.input, [])

        self.space.push(input='hello world')
        self.assertEqual(self.space.input, ['hello world'])

        self.space.push(input=['hello', 'world'])
        self.assertEqual(self.space.input, ['hello world', 'hello', 'world'])

    def test_configure(self):

        logging.info("***** configure")

        clear_env('CHANNEL_DEFAULT_PARTICIPANTS')
        settings = {'space.key': 'my value',}
        self.space.configure(settings=settings)
        self.assertEqual(self.space.context.get('space.title'), 'Collaboration space')
        self.assertEqual(self.space.context.get('space.key'), 'my value')
        self.assertEqual(self.space.context.get('space.participants'), None)

        self.assertEqual(self.space.context.get('server.binding'), None)

        self.space.context.clear()
        settings = {'space.title': 'a title',
                    'space.key': 'my value',}
        self.space.configure(settings=settings)
        self.assertEqual(self.space.context.get('space.title'), 'a title')
        self.assertEqual(self.space.context.get('space.key'), 'my value')
        self.assertEqual(self.space.context.get('space.participants'), None)

    def test_check(self):

        logging.info("***** check")

        self.space.push(input=['hello', 'world'])
        self.space.check()
        self.assertEqual(next(self.space._lines, None), "hello")
        self.assertEqual(next(self.space._lines, None), "world")
        self.assertEqual(next(self.space._lines, None), None)

        original_stdin = sys.stdin
        sys.stdin = io.StringIO(u'hello\nworld\n')

        space = LocalSpace(context=self.context)
        space.check()
        self.assertEqual(next(space._lines, None), u"hello")
        self.assertEqual(next(space._lines, None), u"world")
        self.assertEqual(next(space._lines, None), None)

        sys.stdin = original_stdin

    def test_connect(self):

        logging.info("*** connect")

        self.space.connect()

    def test_list_group_channels(self):

        logging.info("*** list_group_channels")

        channels = self.space.list_group_channels()
        self.assertEqual(len(channels), 1)
        channel = channels[0]
        self.assertEqual(channel.id, '*local')
        self.assertEqual(channel.title, 'Collaboration space')

    def test_create(self):

        logging.info("*** create")

        with self.assertRaises(AssertionError):
            channel = self.space.create(title=None)

        with self.assertRaises(AssertionError):
            channel = self.space.create(title='')

        channel = self.space.create(title='*title')
        self.assertEqual(channel.id, '*local')
        self.assertEqual(channel.title, '*title')

    def test_get_by_title(self):

        logging.info("*** get_by_title")

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_title(None)

        with self.assertRaises(AssertionError):
            channel = self.space.get_by_title('')

        channel = self.space.get_by_title(title='*title')
        self.assertEqual(channel.id, '*local')
        self.assertEqual(channel.title, '*title')

    def test_get_by_id(self):

        logging.info("*** get_by_id")

        with self.assertRaises(AssertionError):
            self.space.get_by_id(None)

        with self.assertRaises(AssertionError):
            self.space.get_by_id('')

        channel = self.space.get_by_id(id='*funky')
        self.assertEqual(channel.id, '*funky')
        self.assertEqual(channel.title, self.space.configured_title())

    def test_update(self):

        logging.info("*** update")

        self.space.update(channel=FakeChannel())

    def test_delete(self):

        logging.info("*** delete")

        self.space.delete(id='*id')

    def test_list_participants(self):

        logging.info("*** list_participants")

        self.space.add_participant(id='*id', person='bob@acme.com')
        self.assertEqual(self.space.list_participants('*id'), ['bob@acme.com'])

    def test_add_participants(self):

        logging.info("*** add_participants")

        with mock.patch.object(self.space,
                               'add_participant') as mocked:

            self.space.add_participants(id='*id', persons=['foo.bar@acme.com'])
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_add_participant(self):

        logging.info("***** add_partcipant")

        self.space.add_participant(id='*id', person='bob@acme.com')
        self.assertEqual(self.space.participants, ['bob@acme.com'])

    def test_remove_participants(self):

        logging.info("*** remove_participants")

        with mock.patch.object(self.space,
                               'remove_participant') as mocked:

            self.space.remove_participants(id='*id', persons=['foo.bar@acme.com'])
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_remove_participant(self):

        logging.info("***** remove_participant")

        self.space.add_participant(id='*id', person='bob@acme.com')
        self.assertEqual(self.space.participants, ['bob@acme.com'])
        self.space.remove_participant(id='*id', person='bob@acme.com')
        self.assertEqual(self.space.participants, [])

    def test_walk_messages(self):

        logging.info("*** walk_messages")

        messages = [x for x in self.space.walk_messages(id='*id')]
        self.assertEqual(messages, [])

    def test_post_message(self):

        logging.info("***** post_message")

        with self.assertRaises(AssertionError):
            self.space.post_message(
                text="What's up, Doc?",
                content="*unsupported",
                file="*unsupported")

        with self.assertRaises(AssertionError):
            self.space.post_message(
                id='*id',
                person='a@b.com',
                text="What's up, Doc?",
                content="*unsupported",
                file="*unsupported")

        self.space.post_message(
            id='*id',
            text="What's up, Doc?",
            content="*unsupported",
            file="*unsupported")

        self.space.post_message(
            person='a@b.com',
            text="What's up, Doc?",
            content="*unsupported",
            file="*unsupported")

    def test_on_start(self):

        logging.info("***** on_start")

        self.space.on_start()

    def test_pull(self):

        logging.info("***** pull")

        self.space.push("hello world")
        self.space.check()
        self.space.pull()
        self.assertEqual(json.loads(self.ears.get()),
                         {'text': 'hello world',
                          'from_id': '*user',
                          'type': 'message',
                          'mentioned_ids': ['*bot'],
                          'channel_id': '*local'})

        original_stdin = sys.stdin
        sys.stdin = io.StringIO(u'hello world')

        space = LocalSpace(context=self.context, ears=self.ears)
        space.check()
        space.pull()
        self.assertEqual(json.loads(self.ears.get()),
                         {'text': u'hello world',
                          'from_id': '*user',
                          'type': 'message',
                          'mentioned_ids': ['*bot'],
                          'channel_id': '*local'})

        sys.stdin = original_stdin

    def test_on_message(self):

        logging.info("***** on_message")

        self.space.on_message({'text': 'hello world'}, self.ears)

        self.assertEqual(json.loads(self.ears.get()),
                         {'from_id': '*user',
                          'mentioned_ids': ['*bot'],
                          'text': 'hello world',
                          'type': 'message',
                          'channel_id': '*local'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
