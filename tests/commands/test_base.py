#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.commands import Command


my_bot = ShellBot(mouth=Queue())
my_bot.shell = Shell(bot=my_bot)


class BaseTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Command(my_bot)

        my_bot.shell.configure(settings={
            u'hello': u'world',
        })
        self.assertEqual(my_bot.context.get('general.hello'), u'world')

        self.assertEqual(c.keyword, None)
        self.assertEqual(c.information_message, None)
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c = Command(my_bot, hello='world')
        self.assertEqual(c.hello, 'world')

    def test_from_base(self):

        logging.info('***** from base')

        c = Command(my_bot)
        c.keyword = u'bâtman'
        c.information_message = u"I'm Bâtman!"
        c.execute()
        self.assertEqual(my_bot.mouth.get().text, c.information_message)
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        class Batcave(Command):
            keyword = u'batcave'
            information_message = u"The Batcave is silent..."

            def execute(self, arguments=None):
                if arguments:
                    my_bot.say(
                        u"The Batcave echoes, '{0}'".format(arguments))
                else:
                    my_bot.say(self.information_message)

        c = Batcave(my_bot)
        c.execute('')
        self.assertEqual(my_bot.mouth.get().text, u"The Batcave is silent...")
        c.execute(u'hello?')
        self.assertEqual(my_bot.mouth.get().text, u"The Batcave echoes, 'hello?'")
        with self.assertRaises(Exception):
            print(my_bot.mouth.get_nowait())

        class Batsignal(Command):
            keyword = u'batsignal'
            information_message = u"NANA NANA NANA NANA"
            information_file = "https://upload.wikimedia.org/wikipedia" \
                               "/en/c/c6/Bat-signal_1989_film.jpg"

            def execute(self, arguments=None):
                my_bot.say(self.information_message,
                           file=c.information_file)

        c = Batsignal(my_bot)
        c.execute()
        item = my_bot.mouth.get()
        self.assertEqual(item.text, c.information_message)
        self.assertEqual(item.file, c.information_file)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
