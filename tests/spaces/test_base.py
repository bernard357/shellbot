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

from shellbot import Context
from shellbot.spaces import Space, LocalSpace


class FakeChannel(object):
    id = '*123'
    title = '*title'
    is_direct = False
    is_moderated = False


class SpaceTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.space = Space(context=self.context)

    def tearDown(self):
        del self.space
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("*** init")

        logging.debug("- default init")
        self.assertEqual(self.space.prefix, 'space')
        self.assertEqual(self.space.ears, None)
        self.assertEqual(self.space.fan, None)

        logging.debug("- unknown parameter")
        space = Space(context=self.context, weird='w')
        with self.assertRaises(AttributeError):
            self.assertEqual(space.weird, 'w')
        self.assertEqual(space.prefix, 'space')

        logging.debug("- extended parameters")
        class ExSpace(Space):
            def on_init(self,
                        prefix='space',
                        ex_token=None,
                        **kwargs):
                self.prefix = prefix
                self.token = ex_token

        space = ExSpace(context=self.context,
                        ears='e',
                        fan='f',
                        ex_token='*token',
                        ex_unknown='*weird')
        self.assertEqual(space.ears, 'e')
        self.assertEqual(space.fan, 'f')
        self.assertEqual(space.token, '*token')
        with self.assertRaises(AttributeError):
            self.assertTrue(space.unknown is not None)
        with self.assertRaises(AttributeError):
            self.assertTrue(space.ex_unknown is not None)

        logging.debug("- initialised via configuration")
        space = LocalSpace(context=self.context, prefix='my.space')
        space.configure({
            'my.space': {
                'title': 'Another title',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
            }
        })
        self.assertEqual(space.prefix, 'my.space')
        self.assertEqual(space.configured_title(), 'Another title')

    def test_on_start(self):

        logging.info("*** on_start")

        self.space.on_start()

    def test_on_stop(self):

        logging.info("*** on_stop")

        self.space.on_stop()

    def test_get(self):

        logging.info("*** get")

        space = LocalSpace(context=self.context, prefix='my.space')
        space.configure({
            'my.space': {
                'title': 'Another title',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
            }
        })
        self.assertEqual(space.get('title'), 'Another title')
        self.assertEqual(
            space.get('participants'),
            ['alan.droit@azerty.org', 'bob.nard@support.tv'])
        self.assertEqual(space.get('*unknown', '*default'), '*default')

    def test_set(self):

        logging.info("*** set")

        space = Space(context=self.context)
        space.prefix = 'a_special_space'

        space.set('id', '*id')
        self.assertEqual(self.context.get('a_special_space.id'), '*id')
        self.assertEqual(space.get('id'), '*id')

        space.set('title', '*title')
        self.assertEqual(self.context.get('a_special_space.title'), '*title')
        self.assertEqual(space.get('title'), '*title')

        space.set('_other', ['a', 'b', 'c'])
        self.assertEqual(self.context.get('a_special_space._other'), ['a', 'b', 'c'])
        self.assertEqual(space.get('_other'), ['a', 'b', 'c'])

    def test_configure(self):

        logging.info("*** configure")

        class ExSpace(Space):
            def check(self):
                self.context.check(self.prefix+'.title', is_mandatory=True)

        settings = {'space.key': 'my value'}

        space = ExSpace(context=self.context)
        with self.assertRaises(KeyError):
            space.configure(settings=settings)

        self.assertEqual(space.context.get('space.title'), None)
        self.assertEqual(space.context.get('space.key'), 'my value')

    def test_configured_title(self):

        logging.info("*** configured_title")

        space = Space(context=self.context, prefix='alien')

        self.assertEqual(space.configured_title(),
                         space.DEFAULT_SPACE_TITLE)

        settings = {'alien.title': 'my channel'}

        space.configure(settings=settings)
        self.assertEqual(self.context.get('alien.title'), 'my channel')
        self.assertEqual(space.prefix, 'alien')
        self.assertEqual(space.get('title'), 'my channel')
        self.assertEqual(space.configured_title(), 'my channel')

    def test_connect(self):

        logging.info("*** connect")

        self.space.connect()

    def test_list_group_channels(self):

        logging.info("*** list_group_channels")

        with self.assertRaises(NotImplementedError):
            channels = self.space.list_group_channels()

    def test_create(self):

        logging.info("*** create")

        with self.assertRaises(NotImplementedError):
            channel = self.space.create(title='*title')

    def test_get_by_title(self):

        logging.info("*** get_by_title")

        with self.assertRaises(AssertionError):
            self.space.get_by_title(None)

        with self.assertRaises(AssertionError):
            self.space.get_by_title('')

        self.assertEqual(self.space.get_by_title(title='*unknown'), None)

    def test_get_by_id(self):

        logging.info("*** get_by_id")

        with self.assertRaises(AssertionError):
            self.space.get_by_id(None)

        with self.assertRaises(AssertionError):
            self.space.get_by_id('')

        self.assertEqual(self.space.get_by_id(id='*unknown'), None)

    def test_get_by_person(self):

        logging.info("*** get_by_person")

        with self.assertRaises(AssertionError):
            self.space.get_by_person(None)

        with self.assertRaises(AssertionError):
            self.space.get_by_person('')

        self.assertEqual(self.space.get_by_person('*unknown'), None)

    def test_update(self):

        logging.info("*** update")

        with self.assertRaises(NotImplementedError):
            self.space.update(channel=FakeChannel())

    def test_delete(self):

        logging.info("*** delete")

        with self.assertRaises(NotImplementedError):
            self.space.delete(id='*id')

    def test_list_participants(self):

        logging.info("*** list_participants")

        with self.assertRaises(NotImplementedError):
            self.space.list_participants(id='*id')

    def test_add_participants(self):

        logging.info("*** add_participants")

        with mock.patch.object(self.space,
                               'add_participant') as mocked:

            self.space.add_participants(id='*id', persons=[])
            self.assertFalse(mocked.called)

        class MySpace(Space):
            def on_init(self):
                self._persons = []

            def add_participant(self, id, person):
                self._persons.append(person)

        space = MySpace(context=self.context)
        space.add_participants(
            id='*id',
            persons=['alice@acme.com', 'bob@acme.com'])

        self.assertEqual(
            space._persons,
            ['alice@acme.com', 'bob@acme.com'])

    def test_add_participant(self):

        logging.info("*** add_participant")

        with self.assertRaises(NotImplementedError):
            self.space.add_participant(id='*id', person='alice@acme.com')

    def test_remove_participants(self):

        logging.info("*** remove_participants")

        with mock.patch.object(self.space,
                               'remove_participant') as mocked:

            self.space.remove_participants(id='*id', persons=[])
            self.assertFalse(mocked.called)

        class MySpace(Space):
            def on_init(self):
                self._persons = ['alice@acme.com', 'bob@acme.com']

            def remove_participant(self, id, person):
                self._persons.remove(person)

        space = MySpace(context=self.context)
        space.remove_participants(
            id='*id',
            persons=['bob@acme.com', 'alice@acme.com'])

        self.assertEqual(space._persons, [])

    def test_remove_participant(self):

        logging.info("*** remove_participant")

        with self.assertRaises(NotImplementedError):
            self.space.remove_participant(id='*id', person='alice@acme.com')

    def test_walk_messages(self):

        logging.info("*** walk_messages")

        with self.assertRaises(NotImplementedError):
            message = next(self.space.walk_messages(id='*id'))

    def test_post_message(self):

        logging.info("*** post_message")

        with self.assertRaises(AssertionError):  # missing id and person
            self.space.post_message(text="What's up, Doc?")

        with self.assertRaises(AssertionError): # too much: id and person
            self.space.post_message(id='1', person='2', text="What's up, Doc?")

        with self.assertRaises(NotImplementedError):
            self.space.post_message(id='*id', text="What's up, Doc?")

        with self.assertRaises(NotImplementedError):
            self.space.post_message(person='a@b.com', text="What's up, Doc?")

    def test_webhook(self):

        logging.info("*** webhook")

        with self.assertRaises(NotImplementedError):
            self.space.webhook()

    def test_register(self):

        logging.info("*** register")

        with self.assertRaises(NotImplementedError):
            self.space.register(hook_url='http://no.where/')

    def test_deregister(self):

        logging.info("*** deregister")

        self.space.deregister()

    def test_start(self):

        logging.info("*** start")

        space = Space(context=self.context)
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

        space = ExSpace(context=self.context)
        space.register = mock.Mock()
        space.pull = mock.Mock()
        space.PULL_INTERVAL = 0.01
        space.start()
        time.sleep(0.1)
        while space._bot_id is None:
            time.sleep(0.1)
        while self.context.get('puller.counter', 0) < 4:
            time.sleep(0.1)
        self.context.set('general.switch', 'off')
        self.assertFalse(space.register.called)
        self.assertEqual(space._bot_id, 123)
        self.assertTrue(self.context.get('puller.counter') > 3)

    def test_run(self):

        logging.info("*** run")

        space = Space(context=self.context)
        space.pull = mock.Mock(side_effect=Exception('TEST'))
        space.run()
        self.assertEqual(self.context.get('puller.counter'), 0)

        space = Space(context=self.context)
        space.pull = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        space.run()
        self.assertEqual(self.context.get('puller.counter'), 0)

    def test_pull(self):

        logging.info("*** pull")

        with self.assertRaises(NotImplementedError):
            self.space.pull()



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
