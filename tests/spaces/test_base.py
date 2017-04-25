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

from shellbot import Context
from shellbot.spaces import Space


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

class SpaceTests(unittest.TestCase):

    def test_init(self):

        logging.info("*** init")

        space = Space()
        self.assertTrue(space.context is not None)
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, '*unknown*')
        self.assertEqual(space.hook_url, None)

        space = Space(context='c', weird='w')
        self.assertEqual(space.context, 'c')
        with self.assertRaises(AttributeError):
            self.assertEqual(space.weird, 'w')
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, '*unknown*')
        self.assertEqual(space.hook_url, None)

        class ExSpace(Space):
            def on_init(self, ex_token=None, ex_ears=None, **kwargs):
                self.token = ex_token
                self.ears = ex_ears

        space = ExSpace(ex_token='*token', ex_ears='e', ex_unknown='*weird')
        self.assertEqual(space.token, '*token')
        self.assertEqual(space.ears, 'e')
        with self.assertRaises(AttributeError):
            self.assertTrue(space.unknown is not None)
        with self.assertRaises(AttributeError):
            self.assertTrue(space.ex_unknown is not None)

    def test_reset(self):

        logging.info("*** reset")

        class ExSpace(Space):
            def on_reset(self):
                self._my_counter = 123

        space = ExSpace()
        self.assertTrue(space.context is not None)
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, '*unknown*')
        self.assertEqual(space.hook_url, None)
        self.assertEqual(space._my_counter, 123)

        space.id = '*id'
        space.title = '*title'
        space.hook_url = '*hook'
        space._my_counter = 456

        space.reset()

        self.assertEqual(space.id, None)
        self.assertEqual(space.title, '*unknown*')
        self.assertEqual(space.hook_url, None)
        self.assertEqual(space._my_counter, 123)

    def test_configure(self):

        logging.info("*** configure")

        class ExSpace(Space):
            def check(self):
                self.context.check(self.prefix+'.title', is_mandatory=True)

        settings = {'space.key': 'my value'}

        space = ExSpace()
        with self.assertRaises(KeyError):
            space.configure(settings=settings)

        self.assertEqual(space.context.get('space.title'), None)
        self.assertEqual(space.context.get('space.key'), 'my value')

        space = ExSpace()
        space.configure(settings=settings, do_check=False)

        self.assertEqual(space.context.get('space.title'), None)
        self.assertEqual(space.context.get('space.key'), 'my value')

    def test_bond_mock(self):

        logging.info("*** bond")

        class ExSpace(Space):
            def on_bond(self):
                self.bonded = True

        space = ExSpace()
        space.lookup_space = mock.Mock(return_value=False)
        space.create_space = mock.Mock()
        space.add_moderator = mock.Mock()
        space.add_participant = mock.Mock()

        space.bond(title='*title',
                   moderators=['who', 'knows'],
                   participants=['not', 'me'])

        space.lookup_space.assert_called_with(title='*title')
        space.create_space.assert_called_with(title='*title')
        space.add_moderator.assert_called_with('knows')
        space.add_participant.assert_called_with('me')
        self.assertTrue(space.bonded)


        space = ExSpace()
        space.configure({
            'space': {
                'title': 'Another title',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
            }
        })
        space.lookup_space = mock.Mock(return_value=False)
        space.create_space = mock.Mock()
        space.add_moderator = mock.Mock()
        space.add_participant = mock.Mock()

        space.bond()

        space.lookup_space.assert_called_with(title='Another title')
        space.create_space.assert_called_with(title='Another title')
        space.add_moderator.assert_called_with('joe.bar@corporation.com')
        space.add_participant.assert_called_with('bob.nard@support.tv')
        self.assertTrue(space.bonded)

    def test_is_ready(self):

        logging.info("*** is_ready")

        space = Space()
        self.assertFalse(space.is_ready)

        space = Space(context=Context({'space.id': '123'}))
        self.assertTrue(space.is_ready)

        space = Space()
        space.id = '*id'
        self.assertTrue(space.is_ready)

    def test_lookup_space(self):

        logging.info("*** lookup_space")

        space = Space()
        self.assertFalse(space.lookup_space(title='*title'))

    def test_create_space(self):

        logging.info("*** create_space")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.create_space(title='*title')

    def test_add_moderators(self):

        logging.info("*** add_moderators")

        space = Space()
        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=[])
            self.assertFalse(mocked.called)

        space = Space()
        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=['foo.bar@acme.com'])
            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_moderator(self):

        logging.info("*** add_moderator")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.add_moderator(person='alice@acme.com')

    def test_add_participants(self):

        logging.info("*** add_participants")

        space = Space()
        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=[])
            self.assertFalse(mocked.called)

        space = Space()
        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=['foo.bar@acme.com'])

            mocked.assert_called_with('foo.bar@acme.com')

    def test_add_participant(self):

        logging.info("*** add_participant")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.add_participant(person='alice@acme.com')

    def test_dispose(self):

        logging.info("*** dispose")

        space = Space()
        space.title = '*title'
        space.delete_space = mock.Mock()
        space.reset = mock.Mock()
        space.dispose()
        space.delete_space.assert_called_with(title='*title')
        self.assertTrue(space.reset.called)

        context = Context(settings={'space.title': 'a room'})
        space = Space(context)
        space.title = None
        space.delete_space = mock.Mock()
        space.reset = mock.Mock()
        space.dispose()
        space.delete_space.assert_called_with(title='a room')
        self.assertTrue(space.reset.called)

        context = Context(settings={'space.title': 'another room'})
        space = Space(context)
        space.title = ''
        space.delete_space = mock.Mock()
        space.reset = mock.Mock()
        space.dispose()
        space.delete_space.assert_called_with(title='another room')
        self.assertTrue(space.reset.called)

    def test_delete_space(self):

        logging.info("*** delete_space")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.delete_space(title='*does*not*exist')

    def test_post_message(self):

        logging.info("*** post_message")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.post_message(text="What's up, Doc?")

    def test_webhook(self):

        logging.info("*** webhook")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.webhook()

    def test_register(self):

        logging.info("*** register")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.register(hook_url='http://no.where/')

    def test_run(self):

        logging.info("*** run")

        space = Space()
        space.register = mock.Mock()
        space.pull = mock.Mock()
        space.run(hook_url='http:/who.knows/')
        space.register.assert_called_with(hook_url='http:/who.knows/')
        self.assertFalse(space.pull.called)

        space = Space()
        space.register = mock.Mock()
        space.pull = mock.Mock()
        space.run()
        time.sleep(0.2)
        space.context.set('general.switch', 'off')
        time.sleep(0.2)
        self.assertFalse(space.register.called)
        self.assertEqual(space.context.get('puller.counter'), 1)

    def test_work(self):

        logging.info("*** work")

        space = Space()
        space.pull = mock.Mock(side_effect=Exception('unexpected exception'))
        space.work()
        self.assertEqual(space.context.get('puller.counter'), 0)

        space = Space()
        space.pull = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        space.work()
        self.assertEqual(space.context.get('puller.counter'), 0)

    def test_pull(self):

        logging.info("*** pull")

        space = Space()
        with self.assertRaises(NotImplementedError):
            space.pull()



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
