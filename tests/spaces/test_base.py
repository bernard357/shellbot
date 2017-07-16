#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.spaces import Space, LocalSpace


my_context = Context()


class SpaceTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("*** init")

        logging.debug("- default init")
        space = Space(context=my_context)
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)

        logging.debug("- unknown parameter")
        space = Space(context=my_context, weird='w')
        with self.assertRaises(AttributeError):
            self.assertEqual(space.weird, 'w')
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)

        logging.debug("- extended parameters")
        class ExSpace(Space):
            def on_init(self,
                        prefix='space',
                        ex_token=None,
                        ex_ears=None,
                        **kwargs):
                self.prefix = prefix
                self.token = ex_token
                self.ears = ex_ears

        space = ExSpace(context=my_context,
                        ex_token='*token',
                        ex_ears='e',
                        ex_unknown='*weird')
        self.assertEqual(space.token, '*token')
        self.assertEqual(space.ears, 'e')
        with self.assertRaises(AttributeError):
            self.assertTrue(space.unknown is not None)
        with self.assertRaises(AttributeError):
            self.assertTrue(space.ex_unknown is not None)

        logging.debug("- initialised via configuration")
        space = LocalSpace(context=my_context, prefix='my.space')
        space.configure({
            'my.space': {
                'title': 'Another title',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
            }
        })
        self.assertEqual(space.prefix, 'my.space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space.configured_title(), 'Another title')

    def test_get(self):

        logging.info("*** get")

        space = Space(context=my_context)
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.get('id'), None)
        self.assertEqual(space.get('id', '*default'), '*default')
        self.assertEqual(space.get('title'), None)
        self.assertEqual(space.get('title', '*default'), '*default')
        self.assertEqual(space.get('_other'), None)
        self.assertEqual(space.get('_other', '*default'), '*default')

    def test_set(self):

        logging.info("*** set")

        space = Space(context=my_context)
        space.prefix = 'a_special_space'

        space.set('id', '*id')
        self.assertEqual(my_context.get('a_special_space.id'), '*id')
        self.assertEqual(space.get('id'), '*id')

        space.set('title', '*title')
        self.assertEqual(my_context.get('a_special_space.title'), '*title')
        self.assertEqual(space.get('title'), '*title')

        space.set('_other', ['a', 'b', 'c'])
        self.assertEqual(my_context.get('a_special_space._other'), ['a', 'b', 'c'])
        self.assertEqual(space.get('_other'), ['a', 'b', 'c'])

    def test_reset(self):

        logging.info("*** reset")

        class ExSpace(Space):
            def on_reset(self):
                self._my_counter = 123

        space = ExSpace(context=my_context)
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space._my_counter, 123)

        space.values['id'] = '*id'
        space.values['title'] = '*title'
        space._my_counter = 456

        self.assertEqual(space.id, '*id')
        self.assertEqual(space.title, '*title')
        self.assertEqual(space._my_counter, 456)

        space.reset()

        self.assertEqual(space.id, None)
        self.assertEqual(space.title, None)
        self.assertEqual(space._my_counter, 123)

    def test_configure(self):

        logging.info("*** configure")

        class ExSpace(Space):
            def check(self):
                self.context.check(self.prefix+'.title', is_mandatory=True)

        settings = {'space.key': 'my value'}

        space = ExSpace(context=my_context)
        with self.assertRaises(KeyError):
            space.configure(settings=settings)

        self.assertEqual(space.context.get('space.title'), None)
        self.assertEqual(space.context.get('space.key'), 'my value')

    def test_configured_title(self):

        logging.info("*** configured_title")

        space = Space(context=my_context, prefix='alien')

        self.assertEqual(space.configured_title(),
                         space.DEFAULT_SPACE_TITLE)

        settings = {'alien.title': 'my room'}

        space.configure(settings=settings)
        self.assertEqual(my_context.get('alien.title'), 'my room')
        self.assertEqual(space.prefix, 'alien')
        self.assertEqual(space.get('title'), 'my room')
        self.assertEqual(space.configured_title(), 'my room')

    def test_connect(self):

        logging.info("*** connect")

        space = Space(context=my_context)
        space.connect()

    def test_bond(self):

        logging.info("*** bond")

        class ExSpace(Space):
            def on_bond(self):
                self.bonded = True

        space = ExSpace(context=my_context)
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

        space = ExSpace(context=my_context)
        space.configure(settings={
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
        space.del_participant = mock.Mock()
        space.bond()

        space.lookup_space.assert_called_with(title='Another title')
        space.create_space.assert_called_with(title='Another title')
        space.add_moderator.assert_called_with('joe.bar@corporation.com')
        space.add_participant.assert_called_with('bob.nard@support.tv')
        self.assertTrue(space.bonded)

    def test_is_ready(self):

        logging.info("*** is_ready")

        space = Space(context=my_context, prefix='a_prefix')
        self.assertFalse(space.is_ready)

        space.values['id'] = '*id'
        self.assertTrue(space.is_ready)

    def test_use_space(self):

        logging.info("*** use_space")

        space = Space(context=my_context)
        self.assertFalse(space.use_space(id='*id'))

    def test_lookup_space(self):

        logging.info("*** lookup_space")

        space = Space(context=my_context)
        self.assertFalse(space.lookup_space(title='*title'))

    def test_create_space(self):

        logging.info("*** create_space")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.create_space(title='*title')

    def test_add_moderators(self):

        logging.info("*** add_moderators")

        space = Space(context=my_context)
        with mock.patch.object(space,
                               'add_moderator') as mocked:

            space.add_moderators(persons=[])
            self.assertFalse(mocked.called)

        class MySpace(Space):
            def on_reset(self):
                self._persons = []

            def add_moderator(self, person):
                self._persons.append(person)

        space = MySpace(context=my_context)
        space.add_moderators(
            persons=['alice@acme.com', 'bob@acme.com'])

        self.assertEqual(
            space._persons,
            ['alice@acme.com', 'bob@acme.com'])

    def test_add_moderator(self):

        logging.info("*** add_moderator")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.add_moderator(person='alice@acme.com')

    def test_add_participants(self):

        logging.info("*** add_participants")

        space = Space(context=my_context)
        with mock.patch.object(space,
                               'add_participant') as mocked:

            space.add_participants(persons=[])
            self.assertFalse(mocked.called)

        class MySpace(Space):
            def on_reset(self):
                self._persons = []

            def add_participant(self, person):
                self._persons.append(person)

        space = MySpace(context=my_context)
        space.add_participants(
            persons=['alice@acme.com', 'bob@acme.com'])

        self.assertEqual(
            space._persons,
            ['alice@acme.com', 'bob@acme.com'])

    def test_add_participant(self):

        logging.info("*** add_participant")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.add_participant(person='alice@acme.com')

    def test_remove_participants(self):

        logging.info("*** remove_participants")

        space = Space(context=my_context)
        with mock.patch.object(space,
                               'remove_participant') as mocked:

            space.remove_participants(persons=[])
            self.assertFalse(mocked.called)

        class MySpace(Space):
            def on_reset(self):
                self._persons = ['alice@acme.com', 'bob@acme.com']

            def remove_participant(self, person):
                self._persons.remove(person)

        space = MySpace(context=my_context)
        space.remove_participants(
            persons=['bob@acme.com', 'alice@acme.com'])

        self.assertEqual(space._persons, [])

    def test_remove_participant(self):

        logging.info("*** remove_participant")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.remove_participant(person='alice@acme.com')

    def test_dispose(self):

        logging.info("*** dispose")

        space = Space(context=my_context)
        space.values['title'] = '*title'
        space.delete_space = mock.Mock()
        space.reset = mock.Mock()
        space.dispose()
        space.delete_space.assert_called_with(title='*title')
        self.assertTrue(space.reset.called)

        my_context.apply(settings={'space.title': 'a room'})
        space = Space(context=my_context)
        space.values['title'] = None
        space.delete_space = mock.Mock()
        space.reset = mock.Mock()
        space.dispose()
        space.delete_space.assert_called_with(title='a room')
        self.assertTrue(space.reset.called)

        my_context.apply(settings={'space.title': 'another room'})
        space = Space(context=my_context)
        space.values['title'] = ''
        space.delete_space = mock.Mock()
        space.reset = mock.Mock()
        space.dispose()
        space.delete_space.assert_called_with(title='another room')
        self.assertTrue(space.reset.called)

    def test_delete_space(self):

        logging.info("*** delete_space")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.delete_space(title='*does*not*exist')

    def test_post_message(self):

        logging.info("*** post_message")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.post_message(text="What's up, Doc?")

    def test_webhook(self):

        logging.info("*** webhook")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.webhook()

    def test_register(self):

        logging.info("*** register")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.register(hook_url='http://no.where/')

    def test_start(self):

        logging.info("*** start")

        space = Space(context=my_context)
        space.register = mock.Mock()
        space.pull = mock.Mock()
        space.start(hook_url='http:/who.knows/')
        space.register.assert_called_with(hook_url='http:/who.knows/')
        self.assertFalse(space.pull.called)

        class ExSpace(Space):
            def on_reset(self):
                self._bot_id = None

            def on_start(self):
                self._bot_id = 123

        space = ExSpace(context=my_context)
        space.register = mock.Mock()
        space.pull = mock.Mock()
        space.PULL_INTERVAL = 0.01
        space.start()
        time.sleep(0.1)
        while space._bot_id is None:
            time.sleep(0.1)
        while my_context.get('puller.counter', 0) < 4:
            time.sleep(0.1)
        my_context.set('general.switch', 'off')
        self.assertFalse(space.register.called)
        self.assertEqual(space._bot_id, 123)
        self.assertTrue(my_context.get('puller.counter') > 3)

    def test_run(self):

        logging.info("*** run")

        space = Space(context=my_context)
        space.pull = mock.Mock(side_effect=Exception('TEST'))
        space.run()
        self.assertEqual(my_context.get('puller.counter'), 0)

        space = Space(context=my_context)
        space.pull = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        space.run()
        self.assertEqual(my_context.get('puller.counter'), 0)

    def test_pull(self):

        logging.info("*** pull")

        space = Space(context=my_context)
        with self.assertRaises(NotImplementedError):
            space.pull()



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
