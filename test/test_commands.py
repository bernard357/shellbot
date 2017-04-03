#!/usr/bin/env python

import unittest
import logging
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.shell import Shell


class CommandsTests(unittest.TestCase):

    def test_base(self):

        settings = {
            'hello': 'world',
        }
        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.base import Command

        c = Command(shell)

        self.assertEqual(c.context.get('general.hello'), 'world')

        with self.assertRaises(NotImplementedError):
            c.keyword
        with self.assertRaises(NotImplementedError):
            c.information_message
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        with self.assertRaises(NotImplementedError):
            c.execute('')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_noop(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.noop import Noop

        c = Noop(shell)

        self.assertEqual(c.keyword, 'pass')
        self.assertEqual(c.information_message, 'Does absolutely nothing.')
        self.assertEqual(c.usage_message, 'pass')
        self.assertTrue(c.is_interactive)
        self.assertTrue(c.is_hidden)

        self.assertTrue(c.execute(''))
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_version(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
        }
        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.version import Version

        c = Version(shell)

        self.assertEqual(c.keyword, 'version')
        self.assertEqual(c.information_message, 'Displays software version.')
        self.assertEqual(c.usage_message, 'version')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        self.assertTrue(c.execute(''))
        self.assertEqual(mouth.get(), 'testy version 17.4.1')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_help(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.help import Help

        c = Help(shell)

        self.assertEqual(c.keyword, 'help')
        self.assertEqual(
            c.information_message,
            'Lists available commands and related usage information.')
        self.assertEqual(c.usage_message, 'help <command>')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        self.assertFalse(c.execute(''))
        self.assertEqual(mouth.get(), 'No command has been found.')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

    def test_help_true(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        shell.load_command('shellbot.commands.help')

        from shellbot.commands.help import Help

        c = Help(shell)

        self.assertTrue(c.execute(''))
        self.assertEqual(
            mouth.get(),
            'help - Lists available commands and related usage information.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(c.execute("help"))
        self.assertEqual(
            mouth.get(),
            'help - Lists available commands and related usage information.')
        self.assertEqual(
            mouth.get(),
            'usage:')
        self.assertEqual(
            mouth.get(),
            'help <command>')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_help_false(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.help import Help

        c = Help(shell)

        self.assertFalse(c.execute(''))
        self.assertEqual(mouth.get(), 'No command has been found.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertFalse(c.execute("*unknown*command*"))
        self.assertEqual(mouth.get(), 'This command is unknown.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        shell.load_command('shellbot.commands.help')

        self.assertFalse(c.execute("*unknown*command*"))
        self.assertEqual(mouth.get(), 'This command is unknown.')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_echo(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.echo import Echo

        c = Echo(shell)

        self.assertEqual(c.keyword, 'echo')
        self.assertEqual(c.information_message, 'Echoes input string.')
        self.assertEqual(c.usage_message, 'echo "a string to be echoed"')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        message = "hello world"
        self.assertTrue(c.execute(message))
        self.assertEqual(mouth.get(), message)
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_sleep(self):

        context = Context()
        mouth = Queue()
        shell = Shell(context, mouth)

        from shellbot.commands.sleep import Sleep

        c = Sleep(shell)

        self.assertEqual(c.keyword, 'sleep')
        self.assertEqual(c.information_message, 'Sleeps for a while.')
        self.assertEqual(c.usage_message, 'sleep <n>')
        self.assertFalse(c.is_interactive)
        self.assertTrue(c.is_hidden)

        self.assertTrue(c.execute(''))
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(c.execute('2'))
        with self.assertRaises(Exception):
            mouth.get_nowait()

if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
