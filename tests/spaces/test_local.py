#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import io
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot
from shellbot.spaces import LocalSpace


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


my_bot = ShellBot()
my_queue = Queue()


class LocalSpaceTests(unittest.TestCase):

    def test_init(self):

        space = LocalSpace(bot=my_bot)
        self.assertEqual(space.prefix, 'local')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, space.DEFAULT_SPACE_TITLE)
        self.assertEqual(space.moderators, [])
        self.assertEqual(space.participants, [])

    def test_on_init(self):

        space = LocalSpace(bot=my_bot)
        self.assertEqual(space.input, [])

        space = LocalSpace(bot=my_bot, input='hello world')
        self.assertEqual(space.input, ['hello world'])

        space = LocalSpace(bot=my_bot, input=['hello', 'world'])
        self.assertEqual(space.input, ['hello', 'world'])

    def test_push(self):

        space = LocalSpace(bot=my_bot)

        space.push(input=None)
        self.assertEqual(space.input, [])

        space.push(input='')
        self.assertEqual(space.input, [])

        space.push(input='hello world')
        self.assertEqual(space.input, ['hello world'])

        space.push(input=['hello', 'world'])
        self.assertEqual(space.input, ['hello world', 'hello', 'world'])

    def test_on_reset(self):

        space = LocalSpace(bot=my_bot, input=["hello", "world"])
        space.on_reset()
        self.assertEqual(next(space._lines, None), "hello")
        self.assertEqual(next(space._lines, None), "world")
        self.assertEqual(next(space._lines, None), None)

        original_stdin = sys.stdin
        sys.stdin = io.StringIO(u'hello\nworld\n')

        space = LocalSpace(bot=my_bot)
        space.on_reset()
        self.assertEqual(next(space._lines, None), u"hello")
        self.assertEqual(next(space._lines, None), u"world")
        self.assertEqual(next(space._lines, None), None)

        sys.stdin = original_stdin

    def test_configure(self):

        my_bot.context = Context()
        settings = {'local.key': 'my value',}
        space = LocalSpace(bot=my_bot)
        space.configure(settings=settings)
        self.assertEqual(space.bot.context.get('local.title'), 'Local space')
        self.assertEqual(space.bot.context.get('local.key'), 'my value')
        self.assertEqual(space.bot.context.get('local.moderators'), [])
        self.assertEqual(space.bot.context.get('local.participants'), [])

        self.assertEqual(space.bot.context.get('server.binding'), None)

        my_bot.context = Context()
        settings = {'local.key': 'my value',}
        space = LocalSpace(bot=my_bot)
        space.configure(settings=settings, do_check=False)
        self.assertEqual(space.bot.context.get('local.title'), None)
        self.assertEqual(space.bot.context.get('local.key'), 'my value')
        self.assertEqual(space.bot.context.get('local.moderators'), None)
        self.assertEqual(space.bot.context.get('local.participants'), None)

        my_bot.context = Context()
        settings = {'local.title': 'a title',
                    'local.key': 'my value',}
        space = LocalSpace(bot=my_bot)
        space.configure(settings=settings)
        self.assertEqual(space.bot.context.get('local.title'), 'a title')
        self.assertEqual(space.bot.context.get('local.key'), 'my value')
        self.assertEqual(space.bot.context.get('local.moderators'), [])
        self.assertEqual(space.bot.context.get('local.participants'), [])

    def test_on_bond(self):

        space = LocalSpace(bot=my_bot)
        space.on_bond()

    def test_lookup_space(self):

        space = LocalSpace(bot=my_bot)
        self.assertTrue(space.lookup_space(title='hello there'))
        self.assertEqual(space.title, 'hello there')
        self.assertEqual(space.id, '*id')

        with self.assertRaises(AssertionError):
            space.lookup_space(title=None)

        with self.assertRaises(AssertionError):
            space.lookup_space(title='')

    def test_create_space(self):

        space = LocalSpace(bot=my_bot)
        space.create_space(title='hello there')
        self.assertEqual(space.title, 'hello there')
        self.assertEqual(space.id, '*id')

        with self.assertRaises(AssertionError):
            space.create_space(title=None)

        with self.assertRaises(AssertionError):
            space.create_space(title='')

    def test_add_moderator(self):

        space = LocalSpace(bot=my_bot)
        space.add_moderator(person='bob@acme.com')
        self.assertEqual(space.moderators, ['bob@acme.com'])

    def test_add_participant(self):

        space = LocalSpace(bot=my_bot)
        space.add_participant(person='bob@acme.com')
        self.assertEqual(space.participants, ['bob@acme.com'])

    def test_delete_space(self):

        space = LocalSpace(bot=my_bot)
        space.delete_space(title='*does*not*exist')

    def test_post_message(self):

        space = LocalSpace(bot=my_bot)
        space.post_message(text="What's up, Doc?",
                           content="*unsupported",
                           file="*unsupported")

    def test_pull(self):

        space = LocalSpace(bot=my_bot, input="hello world")
        my_bot.ears = my_queue
        space.pull()
        space.pull()
        space.pull()
        self.assertEqual(json.loads(my_bot.ears.get()),
                         {'text': 'hello world', 'from_id': '*user', 'type': 'message', 'mentioned_ids': ['*bot']})

        original_stdin = sys.stdin
        sys.stdin = io.StringIO(u'hello world')

        space = LocalSpace(bot=my_bot)
        my_bot.ears = my_queue
        space.pull()
        self.assertEqual(json.loads(my_bot.ears.get()),
                         {'text': u'hello world', 'from_id': '*user', 'type': 'message', 'mentioned_ids': ['*bot']})

        sys.stdin = original_stdin

    def test_on_message(self):

        space = LocalSpace(bot=my_bot)
        space.on_message({'text': 'hello world'}, my_queue)

        self.assertEqual(json.loads(my_queue.get()),
                         {'from_id': '*user',
                          'mentioned_ids': ['*bot'],
                          'text': 'hello world',
                          'type': 'message'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
