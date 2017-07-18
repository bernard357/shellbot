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

from shellbot import Context, Engine, ShellBot
from shellbot.spaces import Space, LocalSpace, SparkSpace
from shellbot.stores import MemoryStore


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

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context,
                             ears=Queue(),
                             mouth=Queue())
        self.space = LocalSpace(context=self.context, ears=self.engine.ears)
        self.space.values['id'] = '*id'
        self.store = MemoryStore(context=self.context)
        self.bot = ShellBot(engine=self.engine, space=self.space, store=self.store)

    def tearDown(self):
        del self.bot
        del self.store
        del self.space
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** init ***')

        bot = ShellBot(engine=self.engine)

        self.assertEqual(bot.engine, self.engine)
        self.assertTrue(bot.space is not None)
        self.assertTrue(bot.store is not None)
        self.assertTrue(bot.fan is not None)
        self.assertTrue(bot.machine is None)

        bot = ShellBot(engine=self.engine,
                       space=self.space,
                       store=self.store,
                       fan='f')

        self.assertEqual(bot.engine, self.engine)
        self.assertEqual(bot.space, self.space)
        self.assertEqual(bot.store, self.store)
        self.assertEqual(bot.fan, 'f')

    def test_on_init(self):

        logging.info('*** on_init ***')

        bot = ShellBot(engine=self.engine, fan='f')
        bot.on_init()

    def test_space_id(self):

        logging.info('*** space_id ***')

        bot = ShellBot(engine=self.engine, fan='f')

        self.assertEqual(bot.space_id, None)

        class MySpace(object):
            id = '123'

        bot.space = MySpace()
        self.assertEqual(bot.space_id, '123')

    def test_bond(self):

        logging.info('*** bond ***')

        bot = ShellBot(engine=self.engine, fan='f')
        bot.space = mock.Mock()
        bot.store = mock.Mock()

        with mock.patch.object(self.engine,
                               'dispatch',
                               return_value=None) as mocked:

            bot.bond(reset=True)
            self.assertTrue(bot.space.delete_space.called)
            self.assertTrue(bot.space.bond.called)
            self.assertTrue(bot.store.bond.called)
            self.assertTrue(self.engine.dispatch.called)

    def test_add_moderators(self):

        logging.info('*** add_moderators ***')

        with mock.patch.object(self.bot.space,
                               'add_moderators',
                               return_value=None) as mocked:
            self.bot.add_moderators(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_add_participants(self):

        logging.info('*** add_participants ***')

        with mock.patch.object(self.bot.space,
                               'add_participants',
                               return_value=None) as mocked:
            self.bot.add_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_remove_participants(self):

        logging.info('*** remove_participants ***')

        with mock.patch.object(self.bot.space,
                               'remove_participants',
                               return_value=None) as mocked:
            self.bot.remove_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_dispose(self):

        logging.info('*** dispose ***')

        with mock.patch.object(self.bot.space,
                               'dispose',
                               return_value=None) as mocked:

            self.bot.dispose(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

        self.context.clear()
        with mock.patch.object(self.bot.space,
                               'delete_space',
                               return_value=None) as mocked:

            self.bot.dispose()
            mocked.assert_called_with(title='Collaboration space')

    def test_say(self):

        logging.info('*** say ***')

        self.bot.say('')
        self.bot.say(None)

        with mock.patch.object(self.engine.mouth,
                               'put',
                               return_value=None) as mocked:

            self.bot.say('test')
            self.bot.say('test', content='test')
            self.bot.say('test', file='test.yaml')

        message_0 = None
        self.bot.say(message_0)
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        message_0 = ''
        self.bot.say(message_0)
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        message_1 = 'hello'
        self.bot.say(message_1)
        self.assertEqual(self.engine.mouth.get().text, message_1)

        message_2 = 'world'
        self.bot.say(message_2)
        self.assertEqual(self.engine.mouth.get().text, message_2)

        message_3 = 'hello'
        content_3 = 'world'
        self.bot.say(message_3, content=content_3)
        item = self.engine.mouth.get()
        self.assertEqual(item.text, message_3)
        self.assertEqual(item.content, content_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        self.bot.say(message_4, file=file_4)
        item = self.engine.mouth.get()
        self.assertEqual(item.text, message_4)
        self.assertEqual(item.content, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        content_5 = 'world'
        file_5 = 'http://some.server/some/file'
        self.bot.say(message_5, content=content_5, file=file_5)
        item = self.engine.mouth.get()
        self.assertEqual(item.text, message_5)
        self.assertEqual(item.content, content_5)
        self.assertEqual(item.file, file_5)

        content_6 = 'life is *good*'
        file_6 = 'http://some.server/some/file'
        self.bot.say(content=content_6, file=file_6)
        item = self.engine.mouth.get()
        self.assertEqual(item.text, None)
        self.assertEqual(item.content, content_6)
        self.assertEqual(item.file, file_6)

        content_7 = 'life is _very_ *good*'
        self.bot.say(content=content_7)
        item = self.engine.mouth.get()
        self.assertEqual(item.text, None)
        self.assertEqual(item.content, content_7)
        self.assertEqual(item.file, None)

    def test_remember(self):

        logging.info('***** remember')

        self.assertEqual(self.bot.recall('sca.lar'), None)
        self.bot.remember('sca.lar', 'test')
        self.assertEqual(self.bot.recall('sca.lar'), 'test')

        self.assertEqual(self.bot.recall('list'), None)
        self.bot.remember('list', ['hello', 'world'])
        self.assertEqual(self.bot.recall('list'), ['hello', 'world'])

        self.assertEqual(self.bot.recall('dict'), None)
        self.bot.remember('dict', {'hello': 'world'})
        self.assertEqual(self.bot.recall('dict'), {'hello': 'world'})

    def test_recall(self):

        logging.info('***** recall')

        # undefined key
        self.assertEqual(self.bot.recall('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(self.bot.recall('hello', whatever), whatever)

        # set the key
        self.bot.remember('hello', 'world')
        self.assertEqual(self.bot.recall('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(self.bot.recall('hello', 'whatever'), 'world')

        # except when set to None
        self.bot.remember('special', None)
        self.assertEqual(self.bot.recall('special', []), [])

    def test_forget(self):

        logging.info('***** forget')

        # set the key and then forget it
        self.bot.remember('hello', 'world')
        self.assertEqual(self.bot.recall('hello'), 'world')
        self.bot.forget('hello')
        self.assertEqual(self.bot.recall('hello'), None)

        # set multiple keys and then forget all of them
        self.bot.remember('hello', 'world')
        self.bot.remember('bunny', "What'up, Doc?")
        self.assertEqual(self.bot.recall('hello'), 'world')
        self.assertEqual(self.bot.recall('bunny'), "What'up, Doc?")
        self.bot.forget()
        self.assertEqual(self.bot.recall('hello'), None)
        self.assertEqual(self.bot.recall('bunny'), None)

    def test_append(self):

        logging.info('***** append')

        self.bot.append('famous', 'hello, world')
        self.bot.append('famous', "What'up, Doc?")
        self.assertEqual(self.bot.recall('famous'),
                         ['hello, world', "What'up, Doc?"])

    def test_update(self):

        logging.info('***** update')

        self.bot.update('input', 'PO#', '1234A')
        self.bot.update('input', 'description', 'part does not fit')
        self.assertEqual(self.bot.recall('input'),
                         {u'PO#': u'1234A', u'description': u'part does not fit'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
