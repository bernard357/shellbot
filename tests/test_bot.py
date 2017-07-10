#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
from multiprocessing import Manager, Process, Queue
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Engine, ShellBot
from shellbot.spaces import Space, LocalSpace, SparkSpace
from shellbot.stores import MemoryStore

my_context = Context()
my_engine = Engine(context=my_context,
                   ears=Queue(),
                   mouth=Queue(),
                   fan='f')
my_space = LocalSpace(context=my_context, ears=my_engine.ears)
my_space.values['id'] = '*id'
my_store = MemoryStore(context=my_context)
my_bot = ShellBot(engine=my_engine, space=my_space, store=my_store)

class MyCounter(object):
    def __init__(self, name='counter'):
        self.name = name
        self.count = 0
    def on_bond(self):
        logging.info('{}.on_bond'.format(self.name))
        self.count += 1
    def on_dispose(self):
        logging.info('{}.on_dispose'.format(self.name))
        self.count += 1
    def __del__(self):
        logging.info('(Deleting {})'.format(self.name))


class BotTests(unittest.TestCase):

    def tearDown(self):
        my_context.clear()
        my_store.forget()
        my_engine.subscribed = {
            'bond': [],       # connected to a space
            'dispose': [],    # space will be destroyed
            'start': [],      # starting bot services
            'stop': [],       # stopping bot services
            'message': [],    # message received (with message)
            'attachment': [], # attachment received (with attachment)
            'join': [],       # joining a space (with person)
            'leave': [],      # leaving a space (with person)
            'enter': [],      # invited to a space (for the bot)
            'exit': [],       # kicked off from a space (for the bot)
            'inbound': [],    # other event received from space (with event)
        }
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** init ***')

        bot = ShellBot(engine=my_engine)

        self.assertEqual(bot.engine, my_engine)
        self.assertTrue(bot.space is None)
        self.assertTrue(bot.store is None)
        self.assertTrue(bot.fan is None)
        self.assertTrue(bot.machine is None)

        bot = ShellBot(engine=my_engine,
                       space=my_space,
                       store=my_store,
                       fan='f')

        self.assertEqual(bot.engine, my_engine)
        self.assertEqual(bot.space, my_space)
        self.assertEqual(bot.store, my_store)
        self.assertEqual(bot.fan, 'f')

    def test_bond(self):

        logging.info('*** bond ***')

        bot = ShellBot(engine=my_engine, fan='f')
        bot.space = mock.Mock()
        bot.store = mock.Mock()

        with mock.patch.object(my_engine,
                               'dispatch',
                               return_value=None) as mocked:

            bot.bond(reset=True)
            self.assertTrue(bot.space.delete_space.called)
            self.assertTrue(bot.space.bond.called)
            self.assertTrue(bot.store.bond.called)
            self.assertTrue(my_engine.dispatch.called)

    def test_add_moderators(self):

        logging.info('*** add_moderators ***')

        with mock.patch.object(my_bot.space,
                               'add_moderators',
                               return_value=None) as mocked:
            my_bot.add_moderators(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_add_participants(self):

        logging.info('*** add_participants ***')

        with mock.patch.object(my_bot.space,
                               'add_participants',
                               return_value=None) as mocked:
            my_bot.add_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_remove_participants(self):

        logging.info('*** remove_participants ***')

        with mock.patch.object(my_bot.space,
                               'remove_participants',
                               return_value=None) as mocked:
            my_bot.remove_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_dispose(self):

        logging.info('*** dispose ***')

        with mock.patch.object(my_bot.space,
                               'dispose',
                               return_value=None) as mocked:

            my_bot.dispose(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

        my_context.clear()
        with mock.patch.object(my_bot.space,
                               'delete_space',
                               return_value=None) as mocked:

            my_bot.dispose()
            mocked.assert_called_with(title='Collaboration space')

    def test_say(self):

        logging.info('*** say ***')

        my_bot.say('')
        my_bot.say(None)

        with mock.patch.object(my_engine.mouth,
                               'put',
                               return_value=None) as mocked:

            my_bot.say('test')
            my_bot.say('test', content='test')
            my_bot.say('test', file='test.yaml')

        message_0 = None
        my_bot.say(message_0)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        message_0 = ''
        my_bot.say(message_0)
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        message_1 = 'hello'
        my_bot.say(message_1)
        self.assertEqual(my_engine.mouth.get().text, message_1)

        message_2 = 'world'
        my_bot.say(message_2)
        self.assertEqual(my_engine.mouth.get().text, message_2)

        message_3 = 'hello'
        content_3 = 'world'
        my_bot.say(message_3, content=content_3)
        item = my_engine.mouth.get()
        self.assertEqual(item.text, message_3)
        self.assertEqual(item.content, content_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        my_bot.say(message_4, file=file_4)
        item = my_engine.mouth.get()
        self.assertEqual(item.text, message_4)
        self.assertEqual(item.content, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        content_5 = 'world'
        file_5 = 'http://some.server/some/file'
        my_bot.say(message_5, content=content_5, file=file_5)
        item = my_engine.mouth.get()
        self.assertEqual(item.text, message_5)
        self.assertEqual(item.content, content_5)
        self.assertEqual(item.file, file_5)

    def test_remember(self):

        logging.info('***** remember')

        self.assertEqual(my_bot.recall('sca.lar'), None)
        my_bot.remember('sca.lar', 'test')
        self.assertEqual(my_bot.recall('sca.lar'), 'test')

        self.assertEqual(my_bot.recall('list'), None)
        my_bot.remember('list', ['hello', 'world'])
        self.assertEqual(my_bot.recall('list'), ['hello', 'world'])

        self.assertEqual(my_bot.recall('dict'), None)
        my_bot.remember('dict', {'hello': 'world'})
        self.assertEqual(my_bot.recall('dict'), {'hello': 'world'})

    def test_recall(self):

        logging.info('***** recall')

        # undefined key
        self.assertEqual(my_bot.recall('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(my_bot.recall('hello', whatever), whatever)

        # set the key
        my_bot.remember('hello', 'world')
        self.assertEqual(my_bot.recall('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(my_bot.recall('hello', 'whatever'), 'world')

        # except when set to None
        my_bot.remember('special', None)
        self.assertEqual(my_bot.recall('special', []), [])

    def test_forget(self):

        logging.info('***** forget')

        # set the key and then forget it
        my_bot.remember('hello', 'world')
        self.assertEqual(my_bot.recall('hello'), 'world')
        my_bot.forget('hello')
        self.assertEqual(my_bot.recall('hello'), None)

        # set multiple keys and then forget all of them
        my_bot.remember('hello', 'world')
        my_bot.remember('bunny', "What'up, Doc?")
        self.assertEqual(my_bot.recall('hello'), 'world')
        self.assertEqual(my_bot.recall('bunny'), "What'up, Doc?")
        my_bot.forget()
        self.assertEqual(my_bot.recall('hello'), None)
        self.assertEqual(my_bot.recall('bunny'), None)

    def test_append(self):

        logging.info('***** append')

        my_bot.append('famous', 'hello, world')
        my_bot.append('famous', "What'up, Doc?")
        self.assertEqual(my_bot.recall('famous'),
                         ['hello, world', "What'up, Doc?"])

    def test_update(self):

        logging.info('***** update')

        my_bot.update('input', 'PO#', '1234A')
        my_bot.update('input', 'description', 'part does not fit')
        self.assertEqual(my_bot.recall('input'),
                         {u'PO#': u'1234A', u'description': u'part does not fit'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
