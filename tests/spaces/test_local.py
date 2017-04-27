#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
import os
from multiprocessing import Process
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


class LocalSpaceTests(unittest.TestCase):

    def test_init(self):

        logging.info("*** init")

        space = LocalSpace(bot=my_bot)
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, space.DEFAULT_SPACE_TITLE)
        self.assertEqual(space.hook_url, None)
        self.assertEqual(space.moderators, [])
        self.assertEqual(space.participants, [])

    def test_configure(self):

        logging.info("*** configure")

        settings = {'space.key': 'my value',}
        space = LocalSpace(bot=my_bot)
        with self.assertRaises(KeyError):
            space.configure(settings=settings)
        self.assertEqual(space.bot.context.get('space.title'), None)
        self.assertEqual(space.bot.context.get('space.key'), 'my value')
        self.assertEqual(space.bot.context.get('space.moderators'), None)
        self.assertEqual(space.bot.context.get('space.participants'), None)

        settings = {'space.key': 'my value',}
        space = LocalSpace(bot=my_bot)
        space.configure(settings=settings, do_check=False)
        self.assertEqual(space.bot.context.get('space.title'), None)
        self.assertEqual(space.bot.context.get('space.key'), 'my value')
        self.assertEqual(space.bot.context.get('space.moderators'), None)
        self.assertEqual(space.bot.context.get('space.participants'), None)

        settings = {'space.title': 'a title',
                    'space.key': 'my value',}
        space = LocalSpace(bot=my_bot)
        space.configure(settings=settings)
        self.assertEqual(space.bot.context.get('space.title'), 'a title')
        self.assertEqual(space.bot.context.get('space.key'), 'my value')
        self.assertEqual(space.bot.context.get('space.moderators'), [])
        self.assertEqual(space.bot.context.get('space.participants'), [])

    def test_on_bond(self):

        logging.info("*** on_bond")

        space = LocalSpace(bot=my_bot)
        space.on_bond()

    def test_lookup_space(self):

        logging.info("*** lookup_space")

        space = LocalSpace(bot=my_bot)
        self.assertTrue(space.lookup_space(title='hello there'))
        self.assertEqual(space.title, 'hello there')
        self.assertEqual(space.id, '*id')

        with self.assertRaises(AssertionError):
            space.lookup_space(title=None)

        with self.assertRaises(AssertionError):
            space.lookup_space(title='')

    def test_create_space(self):

        logging.info("*** create_space")

        space = LocalSpace(bot=my_bot)
        space.create_space(title='hello there')
        self.assertEqual(space.title, 'hello there')
        self.assertEqual(space.id, '*id')

        with self.assertRaises(AssertionError):
            space.create_space(title=None)

        with self.assertRaises(AssertionError):
            space.create_space(title='')

    def test_add_moderator(self):

        logging.info("*** add_moderator")

        space = LocalSpace(bot=my_bot)
        space.add_moderator(person='bob@acme.com')
        self.assertEqual(space.moderators, ['bob@acme.com'])

    def test_add_participant(self):

        logging.info("*** add_participant")

        space = LocalSpace(bot=my_bot)
        space.add_participant(person='bob@acme.com')
        self.assertEqual(space.participants, ['bob@acme.com'])

    def test_delete_space(self):

        logging.info("*** delete_space")

        space = LocalSpace(bot=my_bot)
        space.delete_space(title='*does*not*exist')

    def test_post_message(self):

        logging.info("*** post_message")

        space = LocalSpace(bot=my_bot)
        space.post_message(text="What's up, Doc?")

    def test_pull(self):

        logging.info("*** pull")

        space = LocalSpace(bot=my_bot)
        with self.assertRaises(NotImplementedError):
            space.pull()



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
