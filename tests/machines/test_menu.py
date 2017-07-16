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

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, Engine
from shellbot.machines import Menu
from shellbot.stores import MemoryStore

class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("Injecting test bot")
        return my_bot


my_engine = MyEngine()

class FakeBot(object):
    space_id = '234'
    fan = Queue()

    def __init__(self, engine, store=None):
        self.engine = engine
        self.store = store

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file, self.space_id))

    def update(self, key, label, item):
        self.store.update(key, label, item)

    def recall(self, key, default=None):
        return self.store.recall(key, default)


my_bot = FakeBot(engine=my_engine)


class MenuTests(unittest.TestCase):

    def tearDown(self):
        my_engine.context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("******** init")

        with self.assertRaises(AssertionError):
            machine = Menu(bot=my_bot)  # missing question

        with self.assertRaises(AssertionError):
            machine = Menu(bot=my_bot,  # missing options
                           question="What's up, Doc?")

        with self.assertRaises(AssertionError):
            machine = Menu(bot=my_bot,  # not supported parameter
                           question="What's up, Doc?",
                           options=["option 1", "option 2"],
                           mask="*mask")

        with self.assertRaises(AssertionError):
            machine = Menu(bot=my_bot,  # not supported parameter
                           question="What's up, Doc?",
                           options=["option 1", "option 2"],
                           regex="*regex")

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.bot, my_bot)
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

        machine = Menu(bot=my_bot,
                       question_content="What's *up*, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.question, None)
        self.assertEqual(machine.question_content, "What's *up*, Doc?")
        self.assertEqual(machine.options, [u"option 1", u"option 2"])

        machine = Menu(bot=my_bot,
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
        self.assertEqual(machine.bot, my_bot)
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

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        time.sleep(0.01)
        self.assertTrue(machine.elapsed > 0.01)

    def test_say_answer(self):

        logging.info("******** say_answer")

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

        my_bot = MyBot(engine=my_engine)

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        my_bot.said = []
        machine.say_answer('*test')
        self.assertEqual(
            my_bot.said,
            [machine.ANSWER_MESSAGE])

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       on_answer="ok for {}",
                       on_answer_content="*ok* for {}",
                       on_answer_file="/file/to/upload.pdf",
                       )

        my_bot.said = []
        machine.say_answer('*test')
        self.assertEqual(
            my_bot.said,
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

        my_bot = MyBot(engine=my_engine)

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        my_bot.said = []
        machine.say_retry()
        self.assertEqual(
            my_bot.said,
            [machine.RETRY_MESSAGE])

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       on_retry="please retry",
                       on_retry_content="please *retry*",
                       on_retry_file="/file/to/upload.pdf",
                       )

        my_bot.said = []
        machine.say_retry()
        self.assertEqual(
            my_bot.said,
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

        my_bot = MyBot(engine=my_engine)

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        my_bot.said = []
        machine.say_cancel()
        self.assertEqual(
            my_bot.said,
            [machine.CANCEL_MESSAGE])

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       on_cancel="Ok, forget about it",
                       on_cancel_content="*cancelled*",
                       on_cancel_file="/file/to/upload.pdf",
                       )

        my_bot.said = []
        machine.say_cancel()
        self.assertEqual(
            my_bot.said,
            ['Ok, forget about it', ' ', '*cancelled*', '/file/to/upload.pdf'])

    def test_ask(self):

        logging.info("******** ask")

        class MyBot(FakeBot):

            def say(self, message, **kwargs):
                self.engine.set('said', message)

        my_bot = MyBot(engine=my_engine)

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        machine.listen = mock.Mock()

        machine.ask()
        self.assertEqual(
            my_engine.get('said'),
            "What's up, Doc?\n1. option 1\n2. option 2\n")
        machine.listen.assert_called_with()

    def test_listen(self):

        logging.info("******** listen")

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        my_engine.set('general.switch', 'off')
        p = machine.listen()
        p.join()

    def test_receive(self):

        logging.info("******** receive")

        class MyMenu(Menu):

            def execute(self, arguments):
                if arguments == 'exception':
                    raise Exception('TEST')
                if arguments == 'ctl-c':
                    raise KeyboardInterrupt()
                if arguments == '1':
                    self.set('answer', 'option 1')
                else:
                    self.set('answer', arguments)

        machine = MyMenu(bot=my_bot,
                         question="What's up, Doc?",
                         options=["option 1", "option 2"])

        logging.debug("- with general switch off")
        my_engine.set('general.switch', 'off')
        machine.receive()
        self.assertEqual(machine.get('answer'), None)
        my_engine.set('general.switch', 'on')

        logging.debug("- with is_running false")
        machine.receive()
        self.assertEqual(machine.get('answer'), None)
        machine.set('is_running', True)

        logging.debug("- feed the queue after delay")
        t = Timer(0.1, my_bot.fan.put, ['1'])
        t.start()
        machine.receive()
        self.assertEqual(machine.get('answer'), 'option 1')

        logging.debug("- exit on cancellation time out")
        machine.CANCEL_DELAY = 0.001
        machine.receive()
        self.assertEqual(machine.get('answer'), None)
        machine.CANCEL_DELAY = 40.0

        logging.debug("- exit on poison pill")
        my_bot.fan.put(None)
        machine.receive()
        self.assertEqual(machine.get('answer'), None)

        logging.debug("- exit on regular answer")
        my_bot.fan.put('1')
        machine.receive()
        self.assertEqual(machine.get('answer'), 'option 1')

        logging.debug("- exit on exception")
        my_bot.fan.put('exception')
        machine.receive()
        self.assertEqual(machine.get('answer'), None)

        logging.debug("- exit on keyboard interrupt")
        my_bot.fan.put('ctl-c')
        machine.receive()
        self.assertEqual(machine.get('answer'), None)

    def test_execute(self):

        logging.info("******** execute")

        my_bot = FakeBot(engine=my_engine)
        my_bot.store = mock.Mock()
        my_bot.say = mock.Mock()

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.get('answer'), None)

        machine.step()  # send the question

        machine.step = mock.Mock()

        machine.execute(arguments=None)
        my_bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='')
        my_bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='no option in this response')
        my_bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='1')
        my_bot.say.assert_called_with(machine.ANSWER_MESSAGE)
        self.assertTrue(machine.step.called)

        machine.filter = mock.Mock(return_value=None)
        machine.step = mock.Mock()
        machine.execute(arguments='something else')
        my_bot.say.assert_called_with(machine.RETRY_MESSAGE)
        self.assertFalse(machine.step.called)

    def test_filter(self):

        logging.info("******** filter")

        machine = Menu(bot=my_bot,
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

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        machine.on_input(value='ok!')

    def test_cancel(self):

        logging.info("******** cancel")

        machine = Menu(bot=my_bot,
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

        my_bot = MyBot(engine=my_engine, store=store)

        class MyMenu(Menu):

            def on_input(self, value):
                assert value == 'option 2'

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       key='my.input')

        p = machine.start(tick=0.001)

        time.sleep(0.01)
        my_bot.fan.put('2')
        p.join()

        self.assertEqual(machine.get('answer'), 'option 2')
        self.assertEqual(my_bot.recall('input'), {u'my.input': u'option 2'})

        self.assertEqual(my_engine.get('said'), machine.ANSWER_MESSAGE)

    def test_delayed(self):

        logging.info("******** delayed")

        store = MemoryStore()

        class MyBot(FakeBot):

            def say(self, message):
                self.engine.set('said', message)

        my_bot = MyBot(engine=my_engine, store=store)

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       key='my.input')

        machine.RETRY_DELAY = 0.01
        p = machine.start(tick=0.001)

        time.sleep(0.03)
        my_bot.fan.put('2')
        p.join()

        self.assertEqual(my_bot.recall('input'), {u'my.input': u'option 2'})
        self.assertEqual(my_engine.get('said'), machine.ANSWER_MESSAGE)

    def test_cancelled(self):

        logging.info("******** cancelled")

        class MyBot(FakeBot):

            def say(self, message):
                self.engine.set('said', message)

        my_bot = MyBot(engine=my_engine)
        my_engine.set('my.input', '*void')

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])

        machine.CANCEL_DELAY = 0.02
        machine.RETRY_DELAY = 0.01
        machine.TICK_DURATION = 0.001
        p = machine.start()
        p.join()

        self.assertEqual(my_engine.get('my.input'), '*void')
        self.assertEqual(my_engine.get('said'), machine.CANCEL_MESSAGE)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
