#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Command

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class BaseTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Command(my_engine)

        my_engine.shell.configure(settings={
            u'hello': u'world',
        })
        self.assertEqual(my_engine.get('general.hello'), u'world')

        self.assertEqual(c.keyword, None)
        self.assertEqual(c.information_message, None)
        self.assertEqual(c.usage_message, None)
        self.assertFalse(c.is_hidden)

        c = Command(my_engine, hello='world')
        self.assertEqual(c.hello, 'world')

    def test_execute(self):

        logging.info('***** execute')

        c = Command(my_engine)

        c.execute(my_bot)

        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.keyword = u'bâtman'
        c.information_message = u"I'm Bâtman!"
        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text, c.information_message)

        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

    def test_from_base(self):

        logging.info('***** from base')

        class Batcave(Command):
            keyword = u'batcave'
            information_message = u"The Batcave is silent..."

            def execute(self, bot, arguments=None, **kwargs):
                if arguments:
                    bot.say(
                        u"The Batcave echoes, '{0}'".format(arguments))
                else:
                    bot.say(self.information_message)

        c = Batcave(my_engine)
        c.execute(my_bot, '')
        self.assertEqual(my_engine.mouth.get().text,
                         u"The Batcave is silent...")

        c.execute(my_bot, u'hello?')
        self.assertEqual(my_engine.mouth.get().text,
                         u"The Batcave echoes, 'hello?'")

        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
