#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
from threading import Timer
import time

from shellbot import Context, Engine, Bus
from shellbot.machines import Menu
from shellbot.stores import MemoryStore

class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("Injecting test bot")
        bot = FakeBot(engine=self)
        bot.subscriber = self.bus.subscribe('*id')
        bot.publisher = self.publisher
        return bot

class FakeBot(object):
    id = '234'
    fan = Queue()

    def __init__(self, engine, store=None):
        self.engine = engine
        self.store = store

    def say(self, text=None, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file, self.id))

    def update(self, key, label, item):
        self.store.update(key, label, item)

    def recall(self, key, default=None):
        return self.store.recall(key, default)


class MenuTests(unittest.TestCase):

    def setUp(self):
        self.engine = MyEngine()
        self.engine.bus = Bus(self.engine.context)
        self.engine.bus.check()
        self.engine.publisher = self.engine.bus.publish()
        self.bot = FakeBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

    def tearDown(self):
        del self.bot
        del self.engine.publisher
        del self.engine.bus
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("******** init")

        with self.assertRaises(AssertionError):
            machine = Menu(bot=self.bot)  # missing question

        with self.assertRaises(AssertionError):
            machine = Menu(bot=self.bot,  # missing options
                           question="What's up, Doc?")

        with self.assertRaises(AssertionError):
            machine = Menu(bot=self.bot,  # not supported parameter
                           question="What's up, Doc?",
                           options=["option 1", "option 2"],
                           mask="*mask")

        with self.assertRaises(AssertionError):
            machine = Menu(bot=self.bot,  # not supported parameter
                           question="What's up, Doc?",
                           options=["option 1", "option 2"],
                           regex="*regex")

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.bot, self.bot)
        self.assertEqual(machine.question, "What's up, Doc?")
        self.assertEqual(machine.question_content, None)
        self.assertEqual(machine.options, [u"option 1", u"option 2"])
        self.assertEqual(machine.on_answer, None)
        self.assertEqual(machine.on_answer_content, None)
        self.assertEqual(machine.on_answer_file, None)
        self.assertEqual(machine.on_retry, None)
        self.assertEqual(machine.on_retry_content, None)
        self.assertEqual(machine.on_retry_file, None)
        self.assertEqual(machine.on_cancel, None)
        self.assertEqual(machine.on_cancel_content, None)
        self.assertEqual(machine.on_cancel_file, None)
        self.assertEqual(machine.is_mandatory, False)
        self.assertEqual(machine.key, None)

        self.assertEqual(sorted(machine._states.keys()),
                         ['begin', 'delayed', 'end', 'waiting'])
        self.assertEqual(sorted(machine._transitions.keys()),
                         ['begin', 'delayed', 'waiting'])

        machine = Menu(bot=self.bot,
                       question_content="What's *up*, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.question, None)
        self.assertEqual(machine.question_content, "What's *up*, Doc?")
        self.assertEqual(machine.options, [u"option 1", u"option 2"])

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       question_content="What's *up*, Doc?",
                       options=[u"option 1", u"option 2"],
                       on_answer="ok for {}",
                       on_answer_content="*ok* for {}",
                       on_answer_file="/file/to/upload.pdf",
                       on_retry="please retry",
                       on_retry_content="please *retry*",
                       on_retry_file="/file/to/upload.pdf",
                       on_cancel="Ok, forget about it",
                       on_cancel_content="*cancelled*",
                       on_cancel_file="/file/to/upload.pdf",
                       is_mandatory=True,
                       retry_delay=9,
                       cancel_delay=99,
                       key='rabbit.input')
        self.assertEqual(machine.bot, self.bot)
        self.assertEqual(machine.question, "What's up, Doc?")
        self.assertEqual(machine.question_content, "What's *up*, Doc?")
        self.assertEqual(machine.options, [u"option 1", u"option 2"])
        self.assertEqual(machine.on_answer, "ok for {}")
        self.assertEqual(machine.on_answer_content, "*ok* for {}")
        self.assertEqual(machine.on_answer_file, "/file/to/upload.pdf")
        self.assertEqual(machine.on_retry, "please retry")
        self.assertEqual(machine.on_retry_content, "please *retry*")
        self.assertEqual(machine.on_retry_file, "/file/to/upload.pdf")
        self.assertEqual(machine.on_cancel, "Ok, forget about it")
        self.assertEqual(machine.on_cancel_content, "*cancelled*")
        self.assertEqual(machine.on_cancel_file, "/file/to/upload.pdf")
        self.assertEqual(machine.is_mandatory, True)
        self.assertEqual(machine.RETRY_DELAY, 9)
        self.assertEqual(machine.CANCEL_DELAY, 99)
        self.assertEqual(machine.key, 'rabbit.input')

    def test_elapsed(self):

        logging.info("******** elapsed")

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        time.sleep(0.01)
        self.assertTrue(machine.elapsed > 0.01)

    def test_say_answer(self):

        logging.info("******** say_answer")

        class MyBot(FakeBot):
            def on_init(self):
                self.said = []

            def say(self, message=None, content=None, file=None):
                if message:
                    self.said.append(message)
                if content:
                    self.said.append(content)
                if file:
                    self.said.append(file)

        self.bot = MyBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        self.bot.said = []
        machine.say_answer('*test')
        self.assertEqual(
            self.bot.said,
            [machine.ANSWER_MESSAGE])

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       on_answer="ok for {}",
                       on_answer_content="*ok* for {}",
                       on_answer_file="/file/to/upload.pdf",
                       )

        self.bot.said = []
        machine.say_answer('*test')
        self.assertEqual(
            self.bot.said,
            ['ok for *test', ' ', '*ok* for *test', '/file/to/upload.pdf'])

    def test_say_retry(self):

        logging.info("******** say_retry")

        class MyBot(FakeBot):
            def on_init(self):
                self.said = []

            def say(self, message, content=None, file=None):
                if message:
                    self.said.append(message)
                if content:
                    self.said.append(content)
                if file:
                    self.said.append(file)

        self.bot = MyBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        self.bot.said = []
        machine.say_retry()
        self.assertEqual(
            self.bot.said,
            [machine.RETRY_MESSAGE])

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       on_retry="please retry",
                       on_retry_content="please *retry*",
                       on_retry_file="/file/to/upload.pdf",
                       )

        self.bot.said = []
        machine.say_retry()
        self.assertEqual(
            self.bot.said,
            ['please retry', ' ', 'please *retry*', '/file/to/upload.pdf'])

    def test_say_cancel(self):

        logging.info("******** say_cancel")

        class MyBot(FakeBot):
            def on_init(self):
                self.said = []

            def say(self, message, content=None, file=None):
                if message:
                    self.said.append(message)
                if content:
                    self.said.append(content)
                if file:
                    self.said.append(file)

        self.bot = MyBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        self.bot.said = []
        machine.say_cancel()
        self.assertEqual(
            self.bot.said,
            [machine.CANCEL_MESSAGE])

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       on_cancel="Ok, forget about it",
                       on_cancel_content="*cancelled*",
                       on_cancel_file="/file/to/upload.pdf",
                       )

        self.bot.said = []
        machine.say_cancel()
        self.assertEqual(
            self.bot.said,
            ['Ok, forget about it', ' ', '*cancelled*', '/file/to/upload.pdf'])

    def test_ask(self):

        logging.info("******** ask")

        class MyBot(FakeBot):

            def say(self, text=None, content=None, **kwargs):
                message = content if not text else text
                self.engine.set('said', message)

        self.bot = MyBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        # ask as text
        #
        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        machine.listen = mock.Mock()

        machine.ask()
        self.assertEqual(
            self.engine.get('said'),
            "What's up, Doc?\n1. option 1\n2. option 2\n")
        machine.listen.assert_called_with()

        # ask using Markdown
        #
        machine = Menu(bot=self.bot,
                       question="Where do you want to go?",
                       options=["I want to go North", "Actually, South would be better"],
                       question_content="**Where do you want to go?**\n1. I want to go _North_\n2. Actually, _South_ would be better")
        machine.listen = mock.Mock()

        machine.ask()
        self.assertEqual(
            self.engine.get('said'),
            '**Where do you want to go?**\n1. I want to go _North_\n2. Actually, _South_ would be better')
        machine.listen.assert_called_with()

        # ask using HTML
        #
        machine = Menu(bot=self.bot,
                       question="Where do you want to go?",
                       options=["I want to go North", "Actually, South would be better"],
                       question_content="<h3>Where do you want to go?</h3><ol><li>I want to go North</li><li>Actually, South would be better</li></ol>")
        machine.listen = mock.Mock()

        machine.ask()
        self.assertEqual(
            self.engine.get('said'),
            '<h3>Where do you want to go?</h3><ol><li>I want to go North</li><li>Actually, South would be better</li></ol>')
        machine.listen.assert_called_with()

    def test_listen(self):

        logging.info("******** listen")

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        self.engine.set('general.switch', 'off')
        p = machine.listen()
        p.join()

    def test_receive(self):

        logging.info("******** receive")

        class MyMenu(Menu):

            def execute(self, arguments=None, **kwargs):
                if arguments == 'exception':
                    raise Exception('TEST')
                if arguments == 'ctl-c':
                    raise KeyboardInterrupt()
                if arguments == '1':
                    self.set('answer', 'option 1')
                else:
                    self.set('answer', arguments)

        machine = MyMenu(bot=self.bot,
                         question="What's up, Doc?",
                         options=["option 1", "option 2"])

        logging.debug("- with general switch off")
        self.engine.set('general.switch', 'off')
        machine.receive()
        self.assertEqual(machine.get('answer'), None)
        self.engine.set('general.switch', 'on')

        logging.debug("- with is_running false")
        machine.receive()
        self.assertEqual(machine.get('answer'), None)
        machine.set('is_running', True)

        logging.debug("- feed the queue after delay")
        t = Timer(0.1, self.bot.fan.put, ['1'])
        t.start()
        machine.receive()
        self.assertEqual(machine.get('answer'), 'option 1')

        logging.debug("- exit on poison pill")
        self.bot.fan.put(None)
        machine.receive()
        self.assertEqual(machine.get('answer'), None)

        logging.debug("- exit on regular answer")
        self.bot.fan.put('1')
        machine.receive()
        self.assertEqual(machine.get('answer'), 'option 1')

        logging.debug("- exit on exception")
        self.bot.fan.put('exception')
        machine.receive()
        self.assertEqual(machine.get('answer'), None)

        logging.debug("- exit on keyboard interrupt")
        self.bot.fan.put('ctl-c')
        machine.receive()
        self.assertEqual(machine.get('answer'), None)

    def test_execute(self):

        logging.info("******** execute")

        self.bot = FakeBot(engine=self.engine)
        self.bot.store = mock.Mock()
        self.bot.say = mock.Mock()
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.get('answer'), None)

        machine.step()  # send the question

        machine.step = mock.Mock()

        machine.execute(arguments=None)
        self.bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='')
        self.bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='no option in this response')
        self.bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='1')
        self.bot.say.assert_called_with(machine.ANSWER_MESSAGE)
        self.assertTrue(machine.step.called)

        machine.filter = mock.Mock(return_value=None)
        machine.step = mock.Mock()
        machine.execute(arguments='something else')
        self.bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertFalse(machine.step.called)

    def test_filter(self):

        logging.info("******** filter")

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"])

        self.assertEqual(machine.filter('hello world'), None)
        self.assertEqual(machine.filter('-1'), None)
        self.assertEqual(machine.filter('1.1'), None)
        self.assertEqual(machine.filter('0'), None)
        self.assertEqual(machine.filter('1'), 'option 1')
        self.assertEqual(machine.filter('2'), 'option 2')
        self.assertEqual(machine.filter('3'), None)

    def test_on_input(self):

        logging.info("******** on_input")

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        machine.on_input(value='ok!')

    def test_cancel(self):

        logging.info("******** cancel")

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        machine.say_cancel = mock.Mock()
        machine.stop = mock.Mock()
        machine.cancel()
        self.assertTrue(machine.say_cancel.called)
        self.assertTrue(machine.stop.called)

    def test_cycle(self):

        logging.info("******** life cycle")

        store = MemoryStore()

        class MyBot(FakeBot):

            def say(self, message):
                self.engine.set('said', message)

        self.bot = MyBot(engine=self.engine, store=store)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        class MyMenu(Menu):

            def on_input(self, value):
                assert value == 'option 2'

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       key='my.input')

        p = machine.start(tick=0.001)

        time.sleep(0.01)
        self.bot.fan.put('2')
        p.join()

        self.assertEqual(machine.get('answer'), 'option 2')
        self.assertEqual(self.bot.recall('input'), {u'my.input': u'option 2'})

        self.assertEqual(self.engine.get('said'), machine.ANSWER_MESSAGE)

    def test_delayed(self):

        logging.info("******** delayed")

        store = MemoryStore()

        class MyBot(FakeBot):

            def say(self, message):
                self.engine.set('said', message)

        self.bot = MyBot(engine=self.engine, store=store)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       key='my.input')

        machine.RETRY_DELAY = 0.01
        p = machine.start(tick=0.001)

        time.sleep(0.03)
        self.bot.fan.put('2')
        p.join()

        self.assertEqual(self.bot.recall('input'), {u'my.input': u'option 2'})
        self.assertEqual(self.engine.get('said'), machine.ANSWER_MESSAGE)

    def test_cancelled(self):

        logging.info("******** cancelled")

        class MyBot(FakeBot):

            def say(self, message):
                self.engine.set('said', message)

        self.bot = MyBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher
        self.engine.set('my.input', '*void')

        machine = Menu(bot=self.bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        machine.CANCEL_DELAY = 0.02
        machine.RETRY_DELAY = 0.01
        machine.TICK_DURATION = 0.001
        p = machine.start()
        p.join()

        self.assertEqual(self.engine.get('my.input'), '*void')
        self.assertEqual(self.engine.get('said'), machine.CANCEL_MESSAGE)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
