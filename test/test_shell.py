#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorlog
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


class ShellTests(unittest.TestCase):

    def test_default_properties(self):

        context = Context()
        shell = Shell(context)
        self.assertEqual(shell.name, 'Shelly')
        self.assertEqual(shell.version, '*unknown*')
        self.assertEqual(shell.commands, [])

    def test_set_properties(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
            }

        context = Context(settings)
        shell = Shell(context)
        self.assertEqual(shell.name, 'testy')
        self.assertEqual(shell.version, '17.4.1')

    def test_configure(self):

        logging.debug("*** Configure")

        shell = Shell(context=Context())

        shell.configure({
            'shell': {
                'commands':
                    ['shellbot.commands.help', 'shellbot.commands.noop'],
            }
        })

        self.assertEqual(shell.context.get('shell.commands'),
            ['shellbot.commands.help', 'shellbot.commands.noop'])

    def test_load_command(self):

        context = Context()
        shell = Shell(context)

        shell.load_command('shellbot.commands.help')
        self.assertEqual(shell.commands, ['help'])

        from shellbot.commands.help import Help
        help = Help()
        shell.load_command(help)
        self.assertEqual(help.context, context)
        self.assertEqual(help.shell, shell)
        self.assertEqual(shell.commands, ['help'])
        self.assertEqual(shell.command('help'), help)

    def test_load_commands(self):

        context = Context()
        shell = Shell(context)

        shell.load_commands(['shellbot.commands.help',
                             'shellbot.commands.noop'])
        self.assertEqual(shell.commands, ['help', 'pass'])

        from shellbot.commands.help import Help
        help = Help(shell)
        from shellbot.commands.noop import Noop
        noop = Noop(shell)
        shell.load_commands((help, noop))
        self.assertEqual(shell.commands, ['help', 'pass'])
        self.assertEqual(shell.command('help'), help)
        self.assertEqual(shell.command('pass'), noop)

    def test_load_commands_via_settings(self):

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        context = Context(settings)
        shell = Shell(context)

        self.assertEqual(shell.commands, ['help', 'pass'])

    def test_load_commands_via_configure(self):

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        context = Context()
        shell = Shell(context)
        shell.configure(settings)

        self.assertEqual(
            shell.commands,
            ['*default', '*empty', 'echo', 'help', 'pass', 'sleep', 'version'])

    def test_say(self):

        mouth = Queue()

        context = Context()
        shell = Shell(context, mouth)

        message_0 = None
        shell.say(message_0)
        with self.assertRaises(Exception):
            mouth.get_nowait()

        message_0 = ''
        shell.say(message_0)
        with self.assertRaises(Exception):
            mouth.get_nowait()

        message_1 = 'hello'
        shell.say(message_1)
        self.assertEqual(mouth.get(), message_1)

        message_2 = 'world'
        shell.say(message_2)
        self.assertEqual(mouth.get(), message_2)

        message_3 = 'hello'
        markdown_3 = 'world'
        shell.say(message_3, markdown=markdown_3)
        item = mouth.get()
        self.assertEqual(item.message, message_3)
        self.assertEqual(item.markdown, markdown_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        shell.say(message_4, file=file_4)
        item = mouth.get()
        self.assertEqual(item.message, message_4)
        self.assertEqual(item.markdown, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        markdown_5 = 'world'
        file_5 = 'http://some.server/some/file'
        shell.say(message_5, markdown=markdown_5, file=file_5)
        item = mouth.get()
        self.assertEqual(item.message, message_5)
        self.assertEqual(item.markdown, markdown_5)
        self.assertEqual(item.file, file_5)

    def test_vocabulary(self):

        mouth = Queue()
        inbox = Queue()

        context = Context()
        shell = Shell(context, mouth, inbox)
        shell.load_default_commands()

        self.assertEqual(shell.line, None)
        self.assertEqual(shell.count, 0)

        shell.do('*unknown*')
        self.assertEqual(shell.line, '*unknown*')
        self.assertEqual(shell.count, 1)
        self.assertEqual(mouth.get(),
                         "Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('echo hello world')
        self.assertEqual(shell.line, 'echo hello world')
        self.assertEqual(shell.count, 2)
        self.assertEqual(mouth.get(), 'hello world')
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('help help')
        self.assertEqual(shell.line, 'help help')
        self.assertEqual(shell.count, 3)
        self.assertEqual(mouth.get(),
                         'help - Lists available commands and related usage information.')
        self.assertEqual(mouth.get(), 'usage:')
        self.assertEqual(mouth.get(), 'help <command>')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('pass')
        self.assertEqual(shell.line, 'pass')
        self.assertEqual(shell.count, 4)
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('sleep 123')
        self.assertEqual(shell.line, 'sleep 123')
        self.assertEqual(shell.count, 5)
        context.set('worker.busy', True)
        shell.do('sleep 456')
        self.assertEqual(shell.line, 'sleep 456')
        self.assertEqual(shell.count, 6)
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
        self.assertEqual(shell.line, 'version')
        self.assertEqual(shell.count, 7)
        self.assertEqual(mouth.get(), 'Shelly version *unknown*')
        with self.assertRaises(Exception):
            mouth.get_nowait()
        with self.assertRaises(Exception):
            inbox.get_nowait()

        shell.do('')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 8)
        self.assertEqual(mouth.get(), 'echo - Echoes input string.')
        self.assertEqual(mouth.get(),
                         'help - Lists available commands and related usage information.')
        self.assertEqual(mouth.get(), 'version - Displays software version.')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())
        with self.assertRaises(Exception):
            inbox.get_nowait()

    def test_empty(self):

        mouth = Queue()

        context = Context()
        shell = Shell(context, mouth)

        from shellbot.commands.empty import Empty

        class Doc(Empty):
            def execute(self, *args):
                self.shell.say("What'up Doc?")

        doc = Doc(shell)
        shell.load_command(doc)

        shell.do('')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 1)
        self.assertEqual(mouth.get(), "What'up Doc?")
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        shell.do(None)
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 2)
        self.assertEqual(mouth.get(), "What'up Doc?")
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

    def test_default(self):

        mouth = Queue()

        context = Context()
        shell = Shell(context, mouth)

        from shellbot.commands.default import Default

        class Custom(Default):
            def execute(self, arguments):
                self.shell.say("{}, really?".format(self.shell.verb))

        shell.load_command(Custom(shell))

        shell.do(12345)
        self.assertEqual(shell.line, '12345')
        self.assertEqual(shell.count, 1)
        self.assertEqual(mouth.get(), '12345, really?')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

        shell.do('azerty')
        self.assertEqual(shell.line, 'azerty')
        self.assertEqual(shell.count, 2)
        self.assertEqual(mouth.get(), 'azerty, really?')
        with self.assertRaises(Exception):
            print(mouth.get_nowait())

if __name__ == '__main__':

    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(asctime)-2s %(log_color)s%(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)

    logging.getLogger('').handlers = []
    logging.getLogger('').addHandler(handler)

    logging.getLogger('').setLevel(level=logging.DEBUG)

    sys.exit(unittest.main())
