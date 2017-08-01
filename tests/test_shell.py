#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes


class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("Injecting test bot")
        return MyBot(engine=self)


class MyChannel(object):
    is_direct = False


class MyBot(object):
    channel = MyChannel()

    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


class ShellTests(unittest.TestCase):

    def setUp(self):
        self.engine = MyEngine(mouth=Queue())
        self.engine.configure()
        self.bot = MyBot(engine=self.engine)

    def tearDown(self):
        del self.bot
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        shell = Shell(engine=self.engine)
        self.assertEqual(shell.engine.name, 'Shelly')
        self.assertEqual(shell.engine.version, '*unknown*')
        self.assertEqual(shell.commands, [])

        self.engine.context.apply({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        self.assertEqual(shell.engine.name, 'testy')
        self.assertEqual(shell.engine.version, '17.4.1')
        self.assertEqual(shell.commands, [])

    def test_configure(self):

        logging.info('***** configure')

        shell = Shell(engine=self.engine)

        shell.configure({
            'shell': {
                'commands':
                    ['shellbot.commands.help', 'shellbot.commands.noop'],
            }
        })

        self.assertEqual(shell.engine.get('shell.commands'),
            ['shellbot.commands.help', 'shellbot.commands.noop'])

    def test_load_command(self):

        logging.info('***** load_command')

        shell = Shell(engine=self.engine)
        shell.load_command('this.one.does.not.exist.at.all')
        self.assertEqual(shell.commands, [])

        self.engine.context.clear()
        shell = Shell(engine=self.engine)
        shell.load_command('shellbot.commands.help')
        self.assertEqual(shell.commands, ['help'])

        self.engine.context.clear()
        shell = Shell(engine=self.engine)
        from shellbot.commands.help import Help
        help = Help(self.engine)
        shell.load_command(help)
        self.assertEqual(help.engine, self.engine)
        self.assertEqual(shell.commands, ['help'])
        self.assertEqual(shell.command('help'), help)

    def test_load_commands(self):

        logging.info('***** load_commands')

        shell = Shell(engine=self.engine)

        shell.load_commands(['shellbot.commands.help',
                             'shellbot.commands.noop'])
        self.assertEqual(shell.commands, ['help', 'pass'])

        from shellbot.commands.help import Help
        help = Help(self.engine)
        from shellbot.commands.noop import Noop
        noop = Noop(self.engine)
        shell.load_commands((help, noop))
        self.assertEqual(shell.commands, ['help', 'pass'])
        self.assertEqual(shell.command('help'), help)
        self.assertEqual(shell.command('pass'), noop)

    def test_load_commands_via_configure(self):

        logging.info('***** load_commands via configure')

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        shell = Shell(engine=self.engine)
        shell.configure(settings)

        self.assertEqual(
            shell.commands,
            ['*default', '*empty', 'echo', 'help', 'pass', 'sleep', 'version'])

    def test_vocabulary(self):

        logging.info('***** vocabulary')

        shell = Shell(engine=self.engine)
        shell.load_default_commands()

        self.assertEqual(len(shell.commands), 7)
        self.assertEqual(shell.line, None)
        self.assertEqual(shell.count, 0)

        shell.do('*unknown*', channel_id='*id')
        self.assertEqual(shell.line, '*unknown*')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.engine.mouth.get().text,
                         "Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()

        shell.do('echo hello world', channel_id='*id')
        self.assertEqual(shell.line, 'echo hello world')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.engine.mouth.get().text, 'hello world')
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()

        shell.do('help help', channel_id='*id')
        self.assertEqual(shell.line, 'help help')
        self.assertEqual(shell.count, 3)
        self.assertEqual(shell.engine.mouth.get().text,
                         u'help - Show commands and usage\n'
                         + u'usage: help <command>')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        shell.do('pass', channel_id='*id')
        self.assertEqual(shell.line, 'pass')
        self.assertEqual(shell.count, 4)
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()

        shell.do('sleep .0103', channel_id='*id')
        self.assertEqual(shell.line, 'sleep .0103')
        self.assertEqual(shell.count, 5)
        self.engine.set('worker.busy', True)
        shell.do('sleep .0201', channel_id='*id')
        self.assertEqual(shell.line, 'sleep .0201')
        self.assertEqual(shell.count, 6)
        self.engine.set('worker.busy', False)
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        shell.do('version', channel_id='*id')
        self.assertEqual(shell.line, 'version')
        self.assertEqual(shell.count, 7)
        self.assertEqual(shell.engine.mouth.get().text, u'Shelly version *unknown*')
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()

        shell.do('', channel_id='*id')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 8)
        self.assertEqual(
            shell.engine.mouth.get().text,
            u'Available commands:\n'
            + u'help - Show commands and usage')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

    def test_empty(self):

        logging.info('***** empty')

        shell = Shell(engine=self.engine)

        from shellbot.commands.empty import Empty

        class Doc(Empty):
            def execute(self, bot, arguments=None, **kwargs):
                bot.say("What'up Doc?")

        doc = Doc(self.engine)
        shell.load_command(doc)

        shell.do('', channel_id='*id')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.engine.mouth.get().text, "What'up Doc?")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        shell.do(None, channel_id='*id')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.engine.mouth.get().text, "What'up Doc?")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

    def test_default(self):

        logging.info('***** default')

        shell = Shell(engine=self.engine)

        shell.do(12345, channel_id='*id')
        self.assertEqual(shell.line, '12345')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.engine.mouth.get().text,
                         u"Sorry, I do not know how to handle '12345'")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        from shellbot.commands.default import Default

        class Custom(Default):
            def execute(self, bot, arguments=None, **kwargs):
                bot.say("{}, really?".format(arguments))

        shell.load_command(Custom(self.engine))

        shell.do(12345, channel_id='*id')
        self.assertEqual(shell.line, '12345')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.engine.mouth.get().text, '12345, really?')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        shell.do('azerty', channel_id='*id')
        self.assertEqual(shell.line, 'azerty')
        self.assertEqual(shell.count, 3)
        self.assertEqual(shell.engine.mouth.get().text, 'azerty, really?')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

    def test_in_direct_or_group(self):

        logging.info('***** in_direct or in_group')

        shell = Shell(engine=self.engine)

        from shellbot.commands.base import Command

        class Custom(Command):
            keyword =  'custom'
            def execute(self, bot, arguments=None, **kwargs):
                bot.say("{}, really?".format(arguments))

        shell.load_command(Custom(self.engine))

        self.bot.channel.is_direct = False  # in a group channel

        shell.command('custom').in_direct = False
        shell.command('custom').in_group = False
        shell.do('custom nowhere', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            "Sorry, I do not know how to handle 'custom'")

        shell.command('custom').in_direct = True
        shell.command('custom').in_group = False
        shell.do('custom in_direct', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            "Sorry, I do not know how to handle 'custom'")

        shell.command('custom').in_direct = False
        shell.command('custom').in_group = True
        shell.do('custom in_group', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            'in_group, really?')

        shell.command('custom').in_direct = True
        shell.command('custom').in_group = True
        shell.do('custom both', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            'both, really?')

        self.bot.channel.is_direct = True  # in a direct channel

        shell.command('custom').in_direct = False
        shell.command('custom').in_group = False
        shell.do('custom nowhere', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            "Sorry, I do not know how to handle 'custom'")

        shell.command('custom').in_direct = True
        shell.command('custom').in_group = False
        shell.do('custom in_direct', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            'in_direct, really?')

        shell.command('custom').in_direct = False
        shell.command('custom').in_group = True
        shell.do('custom in_group', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            "Sorry, I do not know how to handle 'custom'")

        shell.command('custom').in_direct = True
        shell.command('custom').in_group = True
        shell.do('custom both', channel_id='*id')
        self.assertEqual(
            shell.engine.mouth.get().text,
            'both, really?')

        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

    def test_exception(self):

        logging.info('***** exception')

        class Intruder(object):
            def keys(self):
                raise Exception('*boom*')

        shell = Shell(engine=self.engine)
        shell._commands = Intruder()

        with self.assertRaises(Exception):
            shell.do(12345, channel_id='*id')

        self.assertEqual(
            shell.engine.mouth.get().text,
            "Sorry, I do not know how to handle '12345'")

        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
