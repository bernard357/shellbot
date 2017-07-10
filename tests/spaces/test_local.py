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

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.spaces import LocalSpace


my_context = Context()
my_ears = Queue()


class LocalSpaceTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        my_context.set('bot.id', '*bot')
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        space = LocalSpace(context=my_context)
        self.assertEqual(space.prefix, 'local')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space.moderators, [])
        self.assertEqual(space.participants, [])

    def test_on_init(self):

        space = LocalSpace(context=my_context)
        self.assertEqual(space.input, [])

        space = LocalSpace(context=my_context, input='hello world')
        self.assertEqual(space.input, ['hello world'])

        space = LocalSpace(context=my_context, input=['hello', 'world'])
        self.assertEqual(space.input, ['hello', 'world'])

    def test_push(self):

        space = LocalSpace(context=my_context)

        space.push(input=None)
        self.assertEqual(space.input, [])

        space.push(input='')
        self.assertEqual(space.input, [])

        space.push(input='hello world')
        self.assertEqual(space.input, ['hello world'])

        space.push(input=['hello', 'world'])
        self.assertEqual(space.input, ['hello world', 'hello', 'world'])

    def test_on_reset(self):

        space = LocalSpace(context=my_context, input=["hello", "world"])
        space.on_reset()
        self.assertEqual(next(space._lines, None), "hello")
        self.assertEqual(next(space._lines, None), "world")
        self.assertEqual(next(space._lines, None), None)

        original_stdin = sys.stdin
        sys.stdin = io.StringIO(u'hello\nworld\n')

        space = LocalSpace(context=my_context)
        space.on_reset()
        self.assertEqual(next(space._lines, None), u"hello")
        self.assertEqual(next(space._lines, None), u"world")
        self.assertEqual(next(space._lines, None), None)

        sys.stdin = original_stdin

    def test_configure(self):

        settings = {'local.key': 'my value',}
        space = LocalSpace(context=my_context)
        space.configure(settings=settings, do_check=True)
        self.assertEqual(space.context.get('local.title'), 'Local space')
        self.assertEqual(space.context.get('local.key'), 'my value')
        self.assertEqual(space.context.get('local.moderators'), [])
        self.assertEqual(space.context.get('local.participants'), [])

        self.assertEqual(space.context.get('server.binding'), None)

        my_context.clear()
        settings = {'local.key': 'my value',}
        space = LocalSpace(context=my_context)
        space.configure(settings=settings, do_check=False)
        self.assertEqual(space.context.get('local.title'), None)
        self.assertEqual(space.context.get('local.key'), 'my value')
        self.assertEqual(space.context.get('local.moderators'), None)
        self.assertEqual(space.context.get('local.participants'), None)

        my_context.clear()
        space = LocalSpace(context=my_context)
        settings = {'local.title': 'a title',
                    'local.key': 'my value',}
        space.configure(settings=settings)
        self.assertEqual(space.context.get('local.title'), 'a title')
        self.assertEqual(space.context.get('local.key'), 'my value')
        self.assertEqual(space.context.get('local.moderators'), [])
        self.assertEqual(space.context.get('local.participants'), [])

    def test_on_bond(self):

        space = LocalSpace(context=my_context)
        space.on_bond()

    def test_use_space(self):

        space = LocalSpace(context=my_context)
        self.assertTrue(space.use_space(id='12357'))
        self.assertEqual(space.title, 'Collaboration space')
        self.assertEqual(space.id, '12357')

        with self.assertRaises(AssertionError):
            space.use_space(id=None)

        with self.assertRaises(AssertionError):
            space.use_space(id='')

    def test_lookup_space(self):

        space = LocalSpace(context=my_context)
        self.assertTrue(space.lookup_space(title='hello there'))
        self.assertEqual(space.title, 'hello there')
        self.assertEqual(space.id, '*id')

        with self.assertRaises(AssertionError):
            space.lookup_space(title=None)

        with self.assertRaises(AssertionError):
            space.lookup_space(title='')

    def test_create_space(self):

        space = LocalSpace(context=my_context)
        space.create_space(title='hello there')
        self.assertEqual(space.title, 'hello there')
        self.assertEqual(space.id, '*id')

        with self.assertRaises(AssertionError):
            space.create_space(title=None)

        with self.assertRaises(AssertionError):
            space.create_space(title='')

    def test_add_moderator(self):

        space = LocalSpace(context=my_context)
        space.add_moderator(person='bob@acme.com')
        self.assertEqual(space.moderators, ['bob@acme.com'])

    def test_add_participant(self):

        space = LocalSpace(context=my_context)
        space.add_participant(person='bob@acme.com')
        self.assertEqual(space.participants, ['bob@acme.com'])

    def test_remove_participant(self):

        space = LocalSpace(context=my_context)
        space.add_participant(person='bob@acme.com')
        self.assertEqual(space.participants, ['bob@acme.com'])
        space.remove_participant(person='bob@acme.com')
        self.assertEqual(space.participants, [])

    def test_delete_space(self):

        space = LocalSpace(context=my_context)
        space.delete_space(title='*does*not*exist')

    def test_post_message(self):

        space = LocalSpace(context=my_context)
        space.post_message(text="What's up, Doc?",
                           content="*unsupported",
                           file="*unsupported",
                           space_id='123')

    def test_on_start(self):

        space = LocalSpace(context=my_context)
        space.on_start()

    def test_pull(self):

        space = LocalSpace(context=my_context,
                           ears=my_ears,
                           input="hello world")
        space.pull()
        space.pull()
        space.pull()
        self.assertEqual(json.loads(my_ears.get_nowait()),
                         {'text': 'hello world', 'from_id': '*user', 'type': 'message', 'mentioned_ids': ['*bot']})

        original_stdin = sys.stdin
        sys.stdin = io.StringIO(u'hello world')

        space = LocalSpace(context=my_context, ears=my_ears)
        space.pull()
        self.assertEqual(json.loads(my_ears.get()),
                         {'text': u'hello world', 'from_id': '*user', 'type': 'message', 'mentioned_ids': ['*bot']})

        sys.stdin = original_stdin

    def test_on_message(self):

        space = LocalSpace(context=my_context)
        space.on_message({'text': 'hello world'}, my_ears)

        self.assertEqual(json.loads(my_ears.get()),
                         {'from_id': '*user',
                          'mentioned_ids': ['*bot'],
                          'text': 'hello world',
                          'type': 'message'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
