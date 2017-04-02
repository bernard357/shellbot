#!/usr/bin/env python

import unittest
import logging
import os
from multiprocessing import Process, Manager, Queue
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.shell import Shell


class SpeakerTests(unittest.TestCase):

    def test_default_properties(self):

        context = Context()
        shell = Shell(context)
        self.assertEqual(shell.name, 'Shelly')
        self.assertEqual(shell.version, '*unknown*')

    def test_set_properties(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
            }

        context = Context(settings)
        shell = Shell(context)
        self.assertEqual(shell.name, 'testy')
        self.assertEqual(shell.version, '17.4.1')

    def test_load_command(self):

        context = Context()
        shell = Shell(context)

        shell.load_command('shellbot.commands.help')
        self.assertEqual(shell.commands.keys(), ['help'])

    def test_load_commands(self):

        context = Context()
        shell = Shell(context)

        shell.load_commands(['shellbot.commands.help',
                             'shellbot.commands.noop'])
        self.assertEqual(shell.commands.keys(), ['help', 'pass'])

    def test_load_commands_via_settings(self):

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        context = Context(settings)
        shell = Shell(context)

        self.assertEqual(shell.commands.keys(), ['help', 'pass'])

    def test_say(self):

        mouth = Queue()

        context = Context()
        shell = Shell(context, mouth)

        message1 = 'hello'
        shell.say(message1)
        message2 = 'world'
        shell.say(message2)
        self.assertEqual(mouth.get(), message1)
        self.assertEqual(mouth.get(), message2)

    def test_vocabulary(self):

        mouth = Queue()
        inbox = Queue()

        context = Context()
        shell = Shell(context, mouth, inbox)
        shell.load_default_commands()

        shell.do('*unknown*')
        self.assertEqual(mouth.get(), "Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('echo hello world')
        self.assertEqual(mouth.get(), 'hello world')
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('help help')
        self.assertEqual(mouth.get(), 'help - Lists available commands and related usage information.')
        self.assertEqual(mouth.get(), 'usage:')
        self.assertEqual(mouth.get(), 'help <command>')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('pass')
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('sleep 123')
        context.set('worker.busy', True)
        shell.do('sleep 456')
        context.set('worker.busy', False)
        self.assertEqual(mouth.get(), 'Ok, working on it')
        self.assertEqual(mouth.get(), 'Ok, will work on it as soon as possible')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())
        (command, arguments) = inbox.get()
        self.assertEqual(command, 'sleep')
        self.assertEqual(arguments, '123')
        (command, arguments) = inbox.get()
        self.assertEqual(command, 'sleep')
        self.assertEqual(arguments, '456')
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('version')
        self.assertEqual(mouth.get(), 'Shelly version *unknown*')
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('')
        self.assertEqual(mouth.get(), 'help - Lists available commands and related usage information.')
        self.assertEqual(mouth.get(), 'version - Displays software version.')
        self.assertEqual(mouth.get(), 'echo - Echoes input string.')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())
        with self.assertRaises(Exception):
            inbox.get_nowait()

if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
