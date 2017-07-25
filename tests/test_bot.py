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

from shellbot import Context, Engine, ShellBot, Bus, Channel
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
        self.engine.bus = Bus(self.context)
        self.engine.bus.check()
        self.engine.publisher = self.engine.bus.publish()
        self.space = LocalSpace(context=self.context, ears=self.engine.ears)
        self.store = MemoryStore(context=self.context)
        self.bot = ShellBot(engine=self.engine,
                            space=self.space,
                            store=self.store)
        self.channel = Channel({'id': '*id', 'title': '*title'})

    def tearDown(self):
        del self.channel
        del self.bot
        del self.store
        del self.space
        del self.engine.publisher
        del self.engine.bus
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
        self.assertTrue(bot.channel is None)
        self.assertFalse(bot.store is None)
        self.assertFalse(bot.fan is None)
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

    def test_is_ready(self):

        logging.info("*** is_ready")

        self.bot.channel = None
        self.assertFalse(self.bot.is_ready)

        self.bot.channel = self.channel
        self.assertTrue(self.bot.is_ready)

    def test_id(self):

        logging.info("*** id")

        self.bot.channel = None
        self.assertEqual(self.bot.id, None)

        self.bot.channel = self.channel
        self.assertEqual(self.bot.id, '*id')

    def test_title(self):

        logging.info("*** title")

        self.bot.channel = None
        self.assertEqual(self.bot.title, None)

        self.bot.channel = self.channel
        self.assertEqual(self.bot.title, '*title')

    def test_reset(self):

        logging.info("*** reset")

        self.bot.channel = self.channel
        self.bot.reset()
        self.assertEqual(self.bot.channel, None)

    def test_on_reset(self):

        logging.info("*** on_reset")

        self.bot.on_reset()

    def test_bond(self):

        logging.info("*** bond")

        self.bot.channel = self.channel
        self.bot.bond()

    def test_on_bond(self):

        logging.info("*** on_bond")

        self.bot.on_bond()

    def test_on_enter(self):

        logging.info("*** on_enter")

        self.bot.on_enter()

    def test_dispose(self):

        logging.info("*** dispose")

        self.engine.dispatch = mock.Mock()
        self.space.delete = mock.Mock()

        self.bot.dispose()
        self.assertFalse(self.engine.dispatch.called)
        self.assertFalse(self.space.delete.called)

        self.bot.channel = self.channel
        self.bot.dispose()
        self.assertTrue(self.engine.dispatch.called)
        self.assertTrue(self.space.delete.called)
        self.assertEqual(self.bot.channel, None)

    def test_on_exit(self):

        logging.info("*** on_exit")

        self.bot.on_exit()

    def test_add_participants(self):

        logging.info('*** add_participants ***')

        self.bot.channel = self.channel
        with mock.patch.object(self.bot.space,
                               'add_participants',
                               return_value=None) as mocked:
            self.bot.add_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(id='*id', persons=['a', 'b', 'c', 'd'])

    def test_add_participant(self):

        logging.info('*** add_participant ***')

        self.bot.channel = self.channel
        with mock.patch.object(self.bot.space,
                               'add_participant',
                               return_value=None) as mocked:
            self.bot.add_participant('foo.bar@acme.com')
            mocked.assert_called_with(id='*id',
                                      is_moderator=False,
                                      person='foo.bar@acme.com')

    def test_remove_participants(self):

        logging.info('*** remove_participants ***')

        self.bot.channel = self.channel
        with mock.patch.object(self.bot.space,
                               'remove_participants',
                               return_value=None) as mocked:
            self.bot.remove_participants(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(id='*id', persons=['a', 'b', 'c', 'd'])

    def test_remove_participant(self):

        logging.info('*** remove_participant ***')

        self.bot.channel = self.channel
        with mock.patch.object(self.bot.space,
                               'remove_participant',
                               return_value=None) as mocked:
            self.bot.remove_participant('foo.bar@acme.com')
            mocked.assert_called_with(id='*id', person='foo.bar@acme.com')

    def test_say(self):

        logging.info('*** say ***')

        self.bot.say('*not*said*because*not*ready')

        self.bot.channel = self.channel

        self.bot.say('')
        self.bot.say(None)

        with mock.patch.object(self.engine.mouth,
                               'put',
                               return_value=None) as mocked:

            self.bot.say('test')
            self.bot.say('test', content='test')
            self.bot.say('test', file='test.yaml')

            self.bot.say('test', person='a@b.com')
            self.bot.say('test', content='test', person='a@b.com')
            self.bot.say('test', file='test.yaml', person='a@b.com')

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
        item = self.engine.mouth.get()
        self.assertEqual(item.text, message_1)
        self.assertEqual(item.channel_id, self.bot.id)
        self.assertEqual(item.person, None)

        self.bot.say(message_1, person='a@b.com')
        item = self.engine.mouth.get()
        self.assertEqual(item.text, message_1)
        self.assertEqual(item.channel_id, None)
        self.assertEqual(item.person, 'a@b.com')

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

    def test_say_banner(self):

        logging.info("*** say_banner")

        self.bot.channel = self.channel

        # banner settings have not been defined at all
        self.context.set('bot.banner.text', None)
        self.context.set('bot.banner.content', None)
        self.context.set('bot.banner.file', None)
        self.bot.say_banner()
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        # banner settings are empty strings
        self.context.set('bot.banner.text', '')
        self.context.set('bot.banner.content', '')
        self.context.set('bot.banner.file', '')
        self.bot.say_banner()
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        # plain banner with text, rich content, and some document upload
        self.context.set('bot.banner.text', u"Type '@{} help' for more information")
        self.context.set('bot.banner.content', u"Type ``@{} help`` for more information")
        self.context.set('bot.banner.file', "http://on.line.doc/guide.pdf")
        self.bot.say_banner()
        item = self.engine.mouth.get()
        self.assertEqual(item.text,
                         "Type '@Shelly help' for more information")
        self.assertEqual(item.content,
                         'Type ``@Shelly help`` for more information')
        self.assertEqual(item.file,
                         'http://on.line.doc/guide.pdf')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

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
