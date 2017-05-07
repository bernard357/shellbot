#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, Shell

my_bot = ShellBot(inbox=Queue(), mouth=Queue())


class ShellTests(unittest.TestCase):

    def test_init(self):

        logging.debug('***** init')

        my_bot.context = Context()
        shell = Shell(bot=my_bot)
        self.assertEqual(shell.bot.name, 'Shelly')
        self.assertEqual(shell.bot.version, '*unknown*')
        self.assertEqual(shell.commands, [])

        context = Context({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        bot = ShellBot(context=context)
        shell = Shell(bot=bot)
        self.assertEqual(shell.bot.name, 'testy')
        self.assertEqual(shell.bot.version, '17.4.1')
        self.assertEqual(shell.commands, [])

    def test_configure(self):

        logging.debug('***** configure')

        my_bot.context = Context()
        shell = Shell(bot=my_bot)

        shell.configure({
            'shell': {
                'commands':
                    ['shellbot.commands.help', 'shellbot.commands.noop'],
            }
        })

        self.assertEqual(shell.bot.context.get('shell.commands'),
            ['shellbot.commands.help', 'shellbot.commands.noop'])

    def test_load_command(self):

        logging.debug('***** load_command')

        my_bot.context = Context()
        shell = Shell(bot=my_bot)
        shell.load_command('this.one.does.not.exist.at.all')
        self.assertEqual(shell.commands, [])

        my_bot.context = Context()
        shell = Shell(bot=my_bot)
        shell.load_command('shellbot.commands.help')
        self.assertEqual(shell.commands, ['help'])

        my_bot.context = Context()
        shell = Shell(bot=my_bot)
        from shellbot.commands.help import Help
        help = Help()
        shell.load_command(help)
        self.assertEqual(help.context, my_bot.context)
        self.assertEqual(help.shell, shell)
        self.assertEqual(help.bot, shell.bot)
        self.assertEqual(shell.commands, ['help'])
        self.assertEqual(shell.command('help'), help)

    def test_load_commands(self):

        logging.debug('***** load_commands')

        my_bot.context = Context()
        shell = Shell(bot=my_bot)

        shell.load_commands(['shellbot.commands.help',
                             'shellbot.commands.noop'])
        self.assertEqual(shell.commands, ['help', 'pass'])

        from shellbot.commands.help import Help
        help = Help(my_bot)
        from shellbot.commands.noop import Noop
        noop = Noop(my_bot)
        shell.load_commands((help, noop))
        self.assertEqual(shell.commands, ['help', 'pass'])
        self.assertEqual(shell.command('help'), help)
        self.assertEqual(shell.command('pass'), noop)

    def test_load_commands_via_settings(self):

        logging.debug('***** load_commands via settings')

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        my_bot.context = Context(settings=settings)
        shell = Shell(bot=my_bot)

        self.assertEqual(shell.commands, ['help', 'pass'])

    def test_load_commands_via_configure(self):

        logging.debug('***** load_commands via configure')

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        my_bot.context = Context()
        shell = Shell(bot=my_bot)
        shell.configure(settings)

        self.assertEqual(
            shell.commands,
            ['*default', '*empty', 'echo', 'help', 'pass', 'sleep', 'version'])

    def test_say(self):

        logging.debug('***** say')

        shell = Shell(bot=my_bot)

        message_0 = None
        shell.say(message_0)
        with self.assertRaises(Exception):
            shell.bot.mouth.get_nowait()

        message_0 = ''
        shell.say(message_0)
        with self.assertRaises(Exception):
            shell.bot.mouth.get_nowait()

        message_1 = 'hello'
        shell.say(message_1)
        self.assertEqual(shell.bot.mouth.get(), message_1)

        message_2 = 'world'
        shell.say(message_2)
        self.assertEqual(shell.bot.mouth.get(), message_2)

        message_3 = 'hello'
        markdown_3 = 'world'
        shell.say(message_3, markdown=markdown_3)
        item = shell.bot.mouth.get()
        self.assertEqual(item.message, message_3)
        self.assertEqual(item.markdown, markdown_3)
        self.assertEqual(item.file, None)

        message_4 = "What'sup Doc?"
        file_4 = 'http://some.server/some/file'
        shell.say(message_4, file=file_4)
        item = shell.bot.mouth.get()
        self.assertEqual(item.message, message_4)
        self.assertEqual(item.markdown, None)
        self.assertEqual(item.file, file_4)

        message_5 = 'hello'
        markdown_5 = 'world'
        file_5 = 'http://some.server/some/file'
        shell.say(message_5, markdown=markdown_5, file=file_5)
        item = shell.bot.mouth.get()
        self.assertEqual(item.message, message_5)
        self.assertEqual(item.markdown, markdown_5)
        self.assertEqual(item.file, file_5)

    def test_vocabulary(self):

        logging.debug('***** vocabulary')

        shell = Shell(bot=my_bot)
        shell.load_default_commands()

        self.assertEqual(len(shell.commands), 7)
        self.assertEqual(shell.line, None)
        self.assertEqual(shell.count, 0)

        shell.do('*unknown*')
        self.assertEqual(shell.line, '*unknown*')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.bot.mouth.get(),
                         "Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            shell.bot.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('echo hello world')
        self.assertEqual(shell.line, 'echo hello world')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.bot.mouth.get(), 'hello world')
        with self.assertRaises(Exception):
            shell.bot.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('help help')
        self.assertEqual(shell.line, 'help help')
        self.assertEqual(shell.count, 3)
        self.assertEqual(shell.bot.mouth.get(),
                         u'help - Show commands and usage\n'
                         + u'usage: help <command>')
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('pass')
        self.assertEqual(shell.line, 'pass')
        self.assertEqual(shell.count, 4)
        with self.assertRaises(Exception):
            shell.bot.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('sleep 123')
        self.assertEqual(shell.line, 'sleep 123')
        self.assertEqual(shell.count, 5)
        shell.bot.context.set('worker.busy', True)
        shell.do('sleep 456')
        self.assertEqual(shell.line, 'sleep 456')
        self.assertEqual(shell.count, 6)
        shell.bot.context.set('worker.busy', False)
        self.assertEqual(shell.bot.mouth.get(), 'Ok, working on it')
        self.assertEqual(shell.bot.mouth.get(),
                         'Ok, will work on it as soon as possible')
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())
        (command, arguments) = shell.bot.inbox.get()
        self.assertEqual(command, 'sleep')
        self.assertEqual(arguments, '123')
        (command, arguments) = shell.bot.inbox.get()
        self.assertEqual(command, 'sleep')
        self.assertEqual(arguments, '456')
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('version')
        self.assertEqual(shell.line, 'version')
        self.assertEqual(shell.count, 7)
        self.assertEqual(shell.bot.mouth.get(), u'Shelly version *unknown*')
        with self.assertRaises(Exception):
            shell.bot.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 8)
        self.assertEqual(
            shell.bot.mouth.get(),
            u'Available commands:\n'
            + u'echo - Echo input string\nhelp - Show commands and usage')
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

    def test_empty(self):

        logging.debug('***** empty')

        shell = Shell(bot=my_bot)

        from shellbot.commands.empty import Empty

        class Doc(Empty):
            def execute(self, *args):
                self.shell.say("What'up Doc?")

        doc = Doc(my_bot)
        shell.load_command(doc)

        shell.do('')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.bot.mouth.get(), "What'up Doc?")
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())

        shell.do(None)
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.bot.mouth.get(), "What'up Doc?")
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())

    def test_default(self):

        logging.debug('***** default')

        shell = Shell(bot=my_bot)

        from shellbot.commands.default import Default

        class Custom(Default):
            def execute(self, arguments):
                self.shell.say("{}, really?".format(arguments))

        shell.load_command(Custom(my_bot))

        shell.do(12345)
        self.assertEqual(shell.line, '12345')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.bot.mouth.get(), '12345, really?')
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())

        shell.do('azerty')
        self.assertEqual(shell.line, 'azerty')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.bot.mouth.get(), 'azerty, really?')
        with self.assertRaises(Exception):
            print(shell.bot.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
