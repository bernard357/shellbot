#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorlog
import unittest
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Shell


class CommandsTests(unittest.TestCase):

    def test_base(self):

        settings = {
            u'hello': u'world',
        }
        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Command

        c = Command(shell)

        self.assertEqual(c.context.get('general.hello'), u'world')

        self.assertEqual(c.keyword, None)
        self.assertEqual(c.information_message, None)
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_from_base(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Command

        c = Command(shell)
        c.keyword = u'bâtman'
        c.information_message = u"I'm Bâtman!"
        c.execute()
        self.assertEqual(mouth.get(), c.information_message)
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        class Batcave(Command):
            keyword = u'batcave'
            information_message = u"The Batcave is silent..."

            def execute(self, arguments=None):
                if arguments:
                    self.shell.say(u"The Batcave echoes, '{0}'".format(arguments))
                else:
                    self.shell.say(self.information_message)

        c = Batcave(shell)
        c.execute('')
        self.assertEqual(mouth.get(), u"The Batcave is silent...")
        c.execute(u'hello?')
        self.assertEqual(mouth.get(), u"The Batcave echoes, 'hello?'")
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        class Batsignal(Command):
            keyword = u'batsignal'
            information_message = u"NANA NANA NANA NANA"
            information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

            def execute(self, arguments=None):
                self.shell.say(self.information_message,
                               file=c.information_file)

        c = Batsignal(shell)
        c.execute()
        item = mouth.get()
        self.assertEqual(item.message, c.information_message)
        self.assertEqual(item.file, c.information_file)

    def test_close(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        class FakeBot(object):
            def __init__(self):
                self.stop = mock.Mock()
                self.dispose = mock.Mock()

        from shellbot.commands import Close

        bot = FakeBot()
        c = Close(shell, bot=bot)

        self.assertEqual(c.keyword, u'close')
        self.assertEqual(c.information_message, u'Close this room.')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), u'Close this room.')
        with self.assertRaises(Exception):
            mouth.get_nowait()
        self.assertTrue(bot.stop.called)
        self.assertTrue(bot.dispose.called)

    def test_default(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Default

        c = Default(shell)

        self.assertEqual(c.keyword, u'*default')
        self.assertEqual(c.information_message, u'Handle unmatched command.')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        shell.verb = u'*unknown*'
        c.execute('test of default command')
        self.assertEqual(mouth.get(),
                         u"Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_echo(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Echo

        c = Echo(shell)

        self.assertEqual(c.keyword, u'echo')
        self.assertEqual(c.information_message, u'Echo input string.')
        self.assertEqual(c.usage_message, u'echo "a string to be echoed"')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        message = u"hello world"
        c.execute(message)
        self.assertEqual(mouth.get(), message)
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_empty(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        shell.load_command('shellbot.commands.help')

        from shellbot.commands import Empty

        c = Empty(shell)

        self.assertEqual(c.keyword, u'*empty')
        self.assertEqual(c.information_message, u'Handle empty command.')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        c.execute()
        self.assertEqual(
            mouth.get(),
            u'help - Show commands and usage.')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

    def test_help(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Help

        c = Help(shell)

        self.assertEqual(c.keyword, u'help')
        self.assertEqual(
            c.information_message,
            u'Show commands and usage.')
        self.assertEqual(c.usage_message, u'help <command>')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), u'No command has been found.')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

    def test_help_true(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        shell.load_command('shellbot.commands.help')

        from shellbot.commands import Help

        c = Help(shell)

        c.execute()
        self.assertEqual(
            mouth.get(),
            u'help - Show commands and usage.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        c.execute("help")
        self.assertEqual(
            mouth.get(),
            u'help - Show commands and usage.')
        self.assertEqual(
            mouth.get(),
            u'usage:')
        self.assertEqual(
            mouth.get(),
            u'help <command>')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_help_false(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Help

        c = Help(shell)

        c.execute()
        self.assertEqual(mouth.get(), u'No command has been found.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        c.execute(u"*unknown*command*")
        self.assertEqual(mouth.get(), u'No command has been found.')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        shell.load_command('shellbot.commands.help')

        c.execute("*unknown*command*")
        self.assertEqual(mouth.get(), u'This command is unknown.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_noop(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Noop

        c = Noop(shell)

        self.assertEqual(c.keyword, u'pass')
        self.assertEqual(c.information_message, u'Do absolutely nothing.')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        c.execute()
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_sleep(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Sleep

        c = Sleep(shell)

        self.assertEqual(c.keyword, u'sleep')
        self.assertEqual(c.information_message, u'Sleep for a while.')
        self.assertEqual(c.usage_message, u'sleep <n>')
        self.assertFalse(c.is_interactive)
        self.assertTrue(c.is_hidden)

        c.execute(u'')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        c.execute(u'1')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_version(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
        }
        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands import Version

        c = Version(shell)

        self.assertEqual(c.keyword, u'version')
        self.assertEqual(c.information_message, u'Display software version.')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'testy version 17.4.1')
        with self.assertRaises(Exception):
            mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
