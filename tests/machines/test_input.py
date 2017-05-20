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

from shellbot import Context, ShellBot
from shellbot.machines import Input
from shellbot.stores import MemoryStore


class InputTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("******** init")

        my_bot = ShellBot()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")
        self.assertEqual(machine.bot, my_bot)
        self.assertEqual(machine.prefix, "machine")
        self.assertEqual(machine.question, "What's up, Doc?")
        self.assertEqual(machine.on_retry, machine.RETRY_MESSAGE)
        self.assertEqual(machine.on_answer, machine.ANSWER_MESSAGE)
        self.assertEqual(machine.on_cancel, machine.CANCEL_MESSAGE)
        self.assertEqual(machine.key, None)

        self.assertEqual(sorted(machine._states.keys()),
                         ['begin', 'delayed', 'end', 'waiting'])
        self.assertEqual(sorted(machine._transitions.keys()),
                         ['begin', 'delayed', 'waiting'])

        machine = Input(bot=my_bot,
                        prefix='who.cares',
                        question="What's up, Doc?",
                        mask="9999A",
                        on_retry="Come on, you can do better! Please retry",
                        on_answer="Thank you, you are doing great",
                        on_cancel="Ok, forget about it",
                        tip=20,
                        timeout=40,
                        key='rabbit.input')
        self.assertEqual(machine.bot, my_bot)
        self.assertEqual(machine.question,
                         "What's up, Doc?")
        self.assertEqual(machine.mask,
                         "9999A")
        self.assertEqual(machine.on_retry,
                         'Come on, you can do better! Please retry')
        self.assertEqual(machine.on_answer,
                         "Thank you, you are doing great")
        self.assertEqual(machine.on_cancel,
                         "Ok, forget about it")
        self.assertEqual(machine.WAIT_DURATION, 20)
        self.assertEqual(machine.CANCEL_DURATION, 40)
        self.assertEqual(machine.key,
                         'rabbit.input')
        self.assertEqual(machine.prefix,
                         "who.cares")

    def test_elapsed(self):

        logging.info("******** elapsed")

        my_bot = ShellBot()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")

        time.sleep(0.01)
        self.assertTrue(machine.elapsed > 0.01)

    def test_ask(self):

        logging.info("******** ask")

        class MyBot(ShellBot):

            def say(self, message):
                self.context.set('said', message)

        my_bot = MyBot()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")
        machine.listen = mock.Mock()

        machine.ask()
        self.assertEqual(my_bot.context.get('said'), machine.question)
        machine.listen.assert_called_with()

    def test_listen(self):

        logging.info("******** listen")

        my_bot = ShellBot()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")

        my_bot.context.set('general.switch', 'off')
        p = machine.listen()
        p.join()

    def test_receive(self):

        logging.info("******** receive")

        my_bot = ShellBot()
        my_bot.fan = Queue()

        class MyInput(Input):

            def execute(self, arguments):
                if arguments == 'exception':
                    raise Exception('TEST')
                if arguments == 'ctl-c':
                    raise KeyboardInterrupt()
                self.set('answer', arguments)

        machine = MyInput(bot=my_bot,
                          question="What's up, Doc?")

        my_bot.context.set('general.switch', 'off')
        machine.receive()  # general switch is off
        self.assertEqual(machine.get('answer'), None)

        my_bot.context.set('general.switch', 'on')

        machine.receive()  # is_running is False
        self.assertEqual(machine.get('answer'), None)

        machine.set('is_running', True)

        t = Timer(0.1, my_bot.fan.put, ['ping'])
        t.start()
        machine.receive()  # exit after delay
        self.assertEqual(machine.get('answer'), 'ping')

        machine.CANCEL_DURATION = 0.0
        machine.receive()  # exit on cancellation
        self.assertEqual(machine.get('answer'), None)

        my_bot.fan.put(None)
        machine.receive()  # exit on poison pill
        self.assertEqual(machine.get('answer'), None)

        my_bot.fan.put('pong')
        machine.receive()  # exit on regular answer
        self.assertEqual(machine.get('answer'), 'pong')

        my_bot.fan.put('exception')
        machine.receive()  # break on Exception
        self.assertEqual(machine.get('answer'), None)

        my_bot.fan.put('ctl-c')
        machine.receive()  # break on KeyboardInterrupt
        self.assertEqual(machine.get('answer'), None)

    def test_execute(self):

        logging.info("******** execute")

        my_bot = ShellBot()
        my_bot.store = mock.Mock()
        my_bot.say = mock.Mock()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?",
                        key='my.key')
        self.assertEqual(machine.get('answer'), None)

        machine.step()  # send the question

        machine.step = mock.Mock()

        machine.execute(arguments=None)
        my_bot.say.assert_called_with(machine.on_retry)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='')
        my_bot.say.assert_called_with(machine.on_retry)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='something at least')
        my_bot.say.assert_called_with(machine.on_answer)
        self.assertTrue(machine.step.called)

        machine.filter = mock.Mock(return_value=None)
        machine.step = mock.Mock()
        machine.execute(arguments='something else')
        my_bot.say.assert_called_with(machine.on_retry)
        self.assertFalse(machine.step.called)

    def test_filter(self):

        logging.info("******** filter")

        my_bot = ShellBot()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")

        self.assertEqual(machine.filter('hello world'), 'hello world')

        machine.mask = '999A'
        self.assertEqual(machine.filter('hello world'), None)

        self.assertEqual(machine.filter('PO: 1324'), '1324')

    def test_search(self):

        logging.info("******** search")

        my_bot = ShellBot()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")

        with self.assertRaises(AssertionError):
            machine.search(None, 'hello world')

        with self.assertRaises(AssertionError):
            machine.search('', 'hello world')

        with self.assertRaises(AssertionError):
            machine.search('999A', None)

        with self.assertRaises(AssertionError):
            machine.search('999A', '')

        self.assertEqual(machine.search('999A', 'hello world'), None)

        self.assertEqual(machine.search('999A', 'PO: 1324'), '1324')

    def test_cancel(self):

        logging.info("******** cancel")

        my_bot = ShellBot()
        my_bot.say = mock.Mock()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?")

        machine.stop = mock.Mock()
        machine.cancel()
        my_bot.say.assert_called_with(machine.on_cancel)
        self.assertTrue(machine.stop.called)

    def test_cycle(self):

        logging.info("******** life cycle")

        store = MemoryStore()

        class MyBot(ShellBot):

            def say(self, message):
                self.context.set('said', message)

        my_bot = MyBot(store=store)
        my_bot.fan = Queue()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?",
                        key='my.input')

        p = machine.start(tick=0.001)

        time.sleep(0.01)
        my_bot.fan.put('here we go')
        p.join()

        self.assertEqual(my_bot.recall('input'), {u'my.input': u'here we go'})
        self.assertEqual(my_bot.context.get('said'), machine.on_answer)

    def test_delayed(self):

        logging.info("******** delayed")

        store = MemoryStore()

        class MyBot(ShellBot):

            def say(self, message):
                self.context.set('said', message)

        my_bot = MyBot(store=store)
        my_bot.fan = Queue()

        machine = Input(bot=my_bot,
                        question="What's up, Doc?",
                        key='my.input')

        machine.WAIT_DURATION = 0.01
        p = machine.start(tick=0.001)

        time.sleep(0.03)
        my_bot.fan.put('here we go')
        p.join()

        self.assertEqual(my_bot.recall('input'), {u'my.input': u'here we go'})
        self.assertEqual(my_bot.context.get('said'), machine.on_answer)

    def test_cancelled(self):

        logging.info("******** cancelled")

        class MyBot(ShellBot):

            def say(self, message):
                self.context.set('said', message)

        my_bot = MyBot()
        my_bot.fan = Queue()
        my_bot.context.set('my.input', '*void')

        machine = Input(bot=my_bot,
                        question="What's up, Doc?",
                        key='my.input')

        machine.CANCEL_DURATION = 0.02
        machine.WAIT_DURATION = 0.01
        machine.TICK_DURATION = 0.001
        p = machine.start()
        p.join()

        self.assertEqual(my_bot.context.get('my.input'), '*void')
        self.assertEqual(my_bot.context.get('said'), machine.on_cancel)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
