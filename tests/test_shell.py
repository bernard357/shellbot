#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Engine, Shell, Vibes


class MyEngine(Engine):
    def get_bot(self, id):
        logging.debug("injecting test bot")
        return Bot(self)


my_engine = MyEngine(inbox=Queue(), mouth=Queue())


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class ShellTests(unittest.TestCase):

    def tearDown(self):
        my_engine.context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.debug('***** init')

        shell = Shell(engine=my_engine)
        self.assertEqual(shell.engine.name, 'Shelly')
        self.assertEqual(shell.engine.version, '*unknown*')
        self.assertEqual(shell.commands, [])

        my_engine.context.apply({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        self.assertEqual(shell.engine.name, 'testy')
        self.assertEqual(shell.engine.version, '17.4.1')
        self.assertEqual(shell.commands, [])

    def test_configure(self):

        logging.debug('***** configure')

        shell = Shell(engine=my_engine)

        shell.configure({
            'shell': {
                'commands':
                    ['shellbot.commands.help', 'shellbot.commands.noop'],
            }
        })

        self.assertEqual(shell.engine.get('shell.commands'),
            ['shellbot.commands.help', 'shellbot.commands.noop'])

    def test_load_command(self):

        logging.debug('***** load_command')

        shell = Shell(engine=my_engine)
        shell.load_command('this.one.does.not.exist.at.all')
        self.assertEqual(shell.commands, [])

        my_engine.context.clear()
        shell = Shell(engine=my_engine)
        shell.load_command('shellbot.commands.help')
        self.assertEqual(shell.commands, ['help'])

        my_engine.context.clear()
        shell = Shell(engine=my_engine)
        from shellbot.commands.help import Help
        help = Help(my_engine)
        shell.load_command(help)
        self.assertEqual(help.engine, my_engine)
        self.assertEqual(shell.commands, ['help'])
        self.assertEqual(shell.command('help'), help)

    def test_load_commands(self):

        logging.debug('***** load_commands')

        shell = Shell(engine=my_engine)

        shell.load_commands(['shellbot.commands.help',
                             'shellbot.commands.noop'])
        self.assertEqual(shell.commands, ['help', 'pass'])

        from shellbot.commands.help import Help
        help = Help(my_engine)
        from shellbot.commands.noop import Noop
        noop = Noop(my_engine)
        shell.load_commands((help, noop))
        self.assertEqual(shell.commands, ['help', 'pass'])
        self.assertEqual(shell.command('help'), help)
        self.assertEqual(shell.command('pass'), noop)

    def test_load_commands_via_settings(self):

        logging.debug('***** load_commands via settings')

        my_engine.context.apply(settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        })

        shell = Shell(engine=my_engine)

        self.assertEqual(shell.commands, ['help', 'pass'])

    def test_load_commands_via_configure(self):

        logging.debug('***** load_commands via configure')

        settings = {
            'shell': {'commands': ['shellbot.commands.help',
                                   'shellbot.commands.noop']},
        }

        shell = Shell(engine=my_engine)
        shell.configure(settings)

        self.assertEqual(
            shell.commands,
            ['*default', '*empty', 'echo', 'help', 'pass', 'sleep', 'version'])

    def test_vocabulary(self):

        logging.debug('***** vocabulary')

        shell = Shell(engine=my_engine)
        shell.load_default_commands()

        self.assertEqual(len(shell.commands), 7)
        self.assertEqual(shell.line, None)
        self.assertEqual(shell.count, 0)

        shell.do('*unknown*', space_id='*id')
        self.assertEqual(shell.line, '*unknown*')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.engine.mouth.get().text,
                         "Sorry, I do not know how to handle '*unknown*'")
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('echo hello world', space_id='*id')
        self.assertEqual(shell.line, 'echo hello world')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.engine.mouth.get().text, 'hello world')
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('help help', space_id='*id')
        self.assertEqual(shell.line, 'help help')
        self.assertEqual(shell.count, 3)
        self.assertEqual(shell.engine.mouth.get().text,
                         u'help - Show commands and usage\n'
                         + u'usage: help <command>')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('pass', space_id='*id')
        self.assertEqual(shell.line, 'pass')
        self.assertEqual(shell.count, 4)
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.bot.inbox.get_nowait()

        shell.do('sleep 123', space_id='*id')
        self.assertEqual(shell.line, 'sleep 123')
        self.assertEqual(shell.count, 5)
        my_engine.set('worker.busy', True)
        shell.do('sleep 456', space_id='*id')
        self.assertEqual(shell.line, 'sleep 456')
        self.assertEqual(shell.count, 6)
        my_engine.set('worker.busy', False)
        self.assertEqual(shell.engine.mouth.get().text, 'Ok, working on it')
        self.assertEqual(shell.engine.mouth.get().text,
                         'Ok, will work on it as soon as possible')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())
        (command, arguments, space_id) = shell.engine.inbox.get()
        self.assertEqual(command, 'sleep')
        self.assertEqual(arguments, '123')
        self.assertEqual(space_id, '*id')
        (command, arguments, space_id) = shell.engine.inbox.get()
        self.assertEqual(command, 'sleep')
        self.assertEqual(arguments, '456')
        self.assertEqual(space_id, '*id')
        with self.assertRaises(Exception):
            shell.engine.inbox.get_nowait()

        shell.do('version', space_id='*id')
        self.assertEqual(shell.line, 'version')
        self.assertEqual(shell.count, 7)
        self.assertEqual(shell.engine.mouth.get().text, u'Shelly version *unknown*')
        with self.assertRaises(Exception):
            shell.engine.mouth.get_nowait()
        with self.assertRaises(Exception):
            shell.engine.inbox.get_nowait()

        shell.do('', space_id='*id')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 8)
        self.assertEqual(
            shell.engine.mouth.get().text,
            u'Available commands:\n'
            + u'help - Show commands and usage')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())
        with self.assertRaises(Exception):
            shell.engine.inbox.get_nowait()

    def test_empty(self):

        logging.debug('***** empty')

        shell = Shell(engine=my_engine)

        from shellbot.commands.empty import Empty

        class Doc(Empty):
            def execute(self, bot, *args):
                bot.say("What'up Doc?")

        doc = Doc(my_engine)
        shell.load_command(doc)

        shell.do('', space_id='*id')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.engine.mouth.get().text, "What'up Doc?")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        shell.do(None, space_id='*id')
        self.assertEqual(shell.line, '')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.engine.mouth.get().text, "What'up Doc?")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

    def test_default(self):

        logging.debug('***** default')

        shell = Shell(engine=my_engine)

        shell.do(12345, space_id='*id')
        logging.debug('*ouch')
        self.assertEqual(shell.line, '12345')
        self.assertEqual(shell.count, 1)
        self.assertEqual(shell.engine.mouth.get().text,
                         u"Sorry, I do not know how to handle '12345'")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        from shellbot.commands.default import Default

        class Custom(Default):
            def execute(self, bot, arguments):
                bot.say("{}, really?".format(arguments))

        shell.load_command(Custom(my_engine))

        shell.do(12345, space_id='*id')
        self.assertEqual(shell.line, '12345')
        self.assertEqual(shell.count, 2)
        self.assertEqual(shell.engine.mouth.get().text, '12345, really?')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

        shell.do('azerty', space_id='*id')
        self.assertEqual(shell.line, 'azerty')
        self.assertEqual(shell.count, 3)
        self.assertEqual(shell.engine.mouth.get().text, 'azerty, really?')
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())

    def test_exception(self):

        logging.debug('***** exception')

        class Intruder(object):
            def keys(self):
                raise Exception('*boom*')

        shell = Shell(engine=my_engine)
        shell._commands = Intruder()

        with self.assertRaises(Exception):
            shell.do(12345, space_id='*id')

        self.assertEqual(shell.engine.mouth.get().text,
                         u"Sorry, I do not know how to handle '12345'")
        with self.assertRaises(Exception):
            print(shell.engine.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
