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
from shellbot.machines import Menu
from shellbot.stores import MemoryStore


class MenuTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def hello(self,event): # Used to test callback function
        return 'hello'

    def test_init(self):

        logging.info("******** init")

        my_bot = ShellBot()

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"])
        self.assertEqual(machine.bot, my_bot)
        self.assertEqual(machine.prefix, "machine")
        self.assertEqual(machine.question, "What's up, Doc?")
        self.assertEqual(machine.options, [u"option 1", u"option 2"])
        self.assertEqual(machine.on_retry, machine.RETRY_MESSAGE)
        self.assertEqual(machine.on_answer, machine.ANSWER_MESSAGE)
        self.assertEqual(machine.on_cancel, machine.CANCEL_MESSAGE)
        self.assertEqual(machine.is_mandatory, machine.IS_MANDATORY)
        self.assertEqual(machine.is_markdown, machine.IS_MARKDOWN)
        self.assertEqual(machine.key, None)

        self.assertEqual(sorted(machine._states.keys()),
                         ['begin', 'delayed', 'end', 'waiting'])
        self.assertEqual(sorted(machine._transitions.keys()),
                         ['begin', 'delayed', 'waiting'])

        machine = Menu(bot=my_bot,
                       prefix='who.cares',
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       on_retry="Come on, you can do better! Please retry",
                       on_answer="Thank you, you are doing great",
                       on_cancel="Ok, forget about it",
                       is_mandatory=0,
                       is_markdown=0,
                       callback=self.hello,
                       tip=20,
                       timeout=40,
                       key='rabbit.menu')
        self.assertEqual(machine.bot, my_bot)
        self.assertEqual(machine.question,
                         "What's up, Doc?")
        self.assertEqual(machine.options,
                         [u"option 1", u"option 2"])
        self.assertEqual(machine.on_retry,
                         'Come on, you can do better! Please retry')
        self.assertEqual(machine.on_answer,
                         "Thank you, you are doing great")
        self.assertEqual(machine.on_cancel,
                         "Ok, forget about it")
        self.assertEqual(machine.is_mandatory, 0)
        self.assertEqual(machine.is_markdown, 0)
        self.assertEqual(machine.callback, self.hello)
        self.assertEqual(machine.WAIT_DURATION, 20)
        self.assertEqual(machine.CANCEL_DURATION, 40)
        self.assertEqual(machine.key,
                         'rabbit.menu')
        self.assertEqual(machine.prefix,
                         "who.cares")

    def test_elapsed(self):

        logging.info("******** elapsed")

        my_bot = ShellBot()

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=["option 1", "option 2"],
                       key='my.menu')

        time.sleep(0.01)
        self.assertTrue(machine.elapsed > 0.005)

    def test_ask(self):

        logging.info("******** ask")

        class MyBot(ShellBot):

            def say(self, message, **kwargs):
                self.context.set('said', message)

        my_bot = MyBot()

        machine = Menu(bot=my_bot,
                       question=u"What's up, Doc?\n1. option 1\n2. option 2",
                       key='my.menu')

        machine.listen = mock.Mock()

        machine.ask()
        self.assertEqual(my_bot.context.get('said'),machine.question)
        machine.listen.assert_called_with()

    def test_listen(self):

        logging.info("******** listen")

        my_bot = ShellBot()

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       key='my.menu')

        my_bot.context.set('general.switch', 'off')
        p = machine.listen()
        p.join()

    def test_receive(self):

        logging.info("******** receive")

        my_bot = ShellBot()
        my_bot.fan = Queue()

        class MyMenu(Menu):

            def execute(self, arguments):
                if arguments == 'exception':
                    raise Exception('TEST')
                if arguments == 'ctl-c':
                    raise KeyboardInterrupt()
                self.set('answer', arguments)

        machine = MyMenu(bot=my_bot,
                         question="What's up, Doc?",
                         options=[u"option 1", u"option 2"],
                         key='my.menu')

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

        machine.CANCEL_DURATION = 0.001
        machine.receive()  # exit on cancellation
        self.assertEqual(machine.get('answer'), None)
        machine.CANCEL_DURATION = 40.0

        my_bot.fan.put(None)
        machine.receive()  # exit on poison pill
        self.assertEqual(machine.get('answer'), None)

        my_bot.fan.put('1')
        machine.receive()  # exit on regular answer
        self.assertEqual(machine.get('answer'), '1')

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

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       callback=self.hello,
                       key='my.key')

        self.assertEqual(machine.get('answer'), None)

        machine.step()  # send the question

        machine.step = mock.Mock()

        machine.execute(arguments=None)
        my_bot.say.assert_called_with(machine.on_retry)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='not acceptable answer')
        my_bot.say.assert_called_with(machine.on_retry)
        self.assertEqual(machine.get('answer'), None)
        self.assertFalse(machine.step.called)

        machine.execute(arguments='1')
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

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"])

        self.assertEqual(machine.filter('hello world'), None)
        self.assertEqual(machine.filter('-1'), None)
        self.assertEqual(machine.filter('1.1'), None)
        self.assertEqual(machine.filter('0'), None)
        self.assertEqual(machine.filter('1'), '1')
        self.assertEqual(machine.filter('2'), '2')
        self.assertEqual(machine.filter('3'), None)

    def test_cancel(self):

        logging.info("******** cancel")

        my_bot = ShellBot()
        my_bot.say = mock.Mock()

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       key='my.menu')

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

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       key='my.menu')

        p = machine.start(tick=0.001)

        time.sleep(0.01)
        my_bot.fan.put('1')
        p.join()
        time.sleep(0.01)

        self.assertEqual(my_bot.recall('input'), {u'my.menu': u'option 1'})
        self.assertEqual(my_bot.context.get('said'), machine.on_answer)

    def test_delayed(self):

        logging.info("******** delayed")

        store = MemoryStore()

        class MyBot(ShellBot):

            def say(self, message):
                self.context.set('said', message)

        my_bot = MyBot(store=store)
        my_bot.fan = Queue()

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       key='my.menu')

        machine.WAIT_DURATION = 0.01
        p = machine.start(tick=0.001)

        time.sleep(0.03)
        my_bot.fan.put('1')
        p.join()

        self.assertEqual(my_bot.recall('input'), {u'my.menu': u'option 1'})
        self.assertEqual(my_bot.context.get('said'), machine.on_answer)

    def test_cancelled(self):

        logging.info("******** cancelled")

        class MyBot(ShellBot):

            def say(self, message):
                self.context.set('said', message)

        my_bot = MyBot()
        my_bot.fan = Queue()
        my_bot.context.set('my.menu', '*void')

        machine = Menu(bot=my_bot,
                       question="What's up, Doc?",
                       options=[u"option 1", u"option 2"],
                       key='my.menu')

        machine.CANCEL_DURATION = 0.02
        machine.WAIT_DURATION = 0.01
        machine.TICK_DURATION = 0.001
#        p = machine.start()
#        p.join()
#
#        self.assertEqual(my_bot.context.get('my.menu'), '*void')
#        self.assertEqual(my_bot.context.get('said'), machine.on_cancel)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
