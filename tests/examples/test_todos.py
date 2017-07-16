#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, Engine, ShellBot, SpaceFactory
from examples.todos import TodoFactory, Done, Drop, History, Next, Todo, Todos


my_settings = {

    'todos.items': [
        'write down the driving question',
        'gather facts and related information',
        'identify information gaps and document assumptions',
        'formulate scenarios',
        'select the most appropriate scenario',
    ],

}

my_context = Context(settings=my_settings)
my_engine = Engine(context=my_context,
                   mouth=Queue(),
                   space=SpaceFactory.get('local'))
my_engine.factory = TodoFactory(my_engine.get('todos.items', []))
my_bot = ShellBot(engine=my_engine)


class TodosTests(unittest.TestCase):

    def setUp(self):
        my_engine.factory.items = my_engine.get('todos.items', [])
        my_engine.factory.archive = []

    def test_commands(self):

        commands = TodoFactory.commands()
        self.assertTrue(len(commands) == 6)
        for command in commands:
            self.assertTrue(command.keyword in ['done', 'drop', 'history', 'next', 'todo', 'todos'])
            self.assertTrue(len(command.information_message) > 1)

    def test_done(self):

        c = Done(engine=my_engine)

        self.assertEqual(c.keyword, 'done')
        self.assertEqual(c.information_message,
                         u'Archive an item from the todo list')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)

        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='#2')

        self.assertEqual(my_engine.mouth.get().text,
                         u'#2 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='#2222')

        self.assertEqual(my_engine.mouth.get().text,
                         u'usage: done [#<n>]')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='nonsense')

        self.assertEqual(my_engine.mouth.get().text,
                         u'usage: done [#<n>]')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_drop(self):

        c = Drop(engine=my_engine)

        self.assertEqual(c.keyword, 'drop')
        self.assertEqual(c.information_message,
                         u'Delete an item from the todo list')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)

        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been deleted')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='#2')

        self.assertEqual(my_engine.mouth.get().text,
                         u'#2 has been deleted')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='#2222')

        self.assertEqual(my_engine.mouth.get().text,
                         u'usage: drop [#<n>]')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='nonsense')

        self.assertEqual(my_engine.mouth.get().text,
                         u'usage: drop [#<n>]')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_history(self):

        Done(engine=my_engine).execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')

        Done(engine=my_engine).execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')

        c = History(engine=my_engine)

        self.assertEqual(c.keyword, 'history')
        self.assertEqual(c.information_message,
                         u'List archived items')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Items that have been archived:\n'
                         + u'- write down the driving question\n'
                         + u'- gather facts and related information')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='whatever')
        self.assertEqual(my_engine.mouth.get().text,
                         u'Items that have been archived:\n'
                         + u'- write down the driving question\n'
                         + u'- gather facts and related information')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_next(self):

        c = Next(engine=my_engine)

        self.assertEqual(c.keyword, 'next')
        self.assertEqual(c.information_message,
                         u'Display next item to do')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)

        self.assertEqual(my_engine.mouth.get().text,
                         u'Coming next: write down the driving question')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='whatever')

        self.assertEqual(my_engine.mouth.get().text,
                         u'Coming next: write down the driving question')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_todo(self):

        my_engine.factory.items = []

        c = Todo(engine=my_engine)

        self.assertEqual(c.keyword, 'todo')
        self.assertEqual(c.information_message,
                         u'Append an item to the todo list, or change it')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)  # no argument

        self.assertEqual(my_engine.mouth.get().text,
                         u'usage: todo [#n] <something to do>')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='#2 something to do')  # target does not exist

        self.assertEqual(my_engine.mouth.get().text,
                         u'usage: todo [#n] <something to do>')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='something to do')  # item creation

        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 something to do')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='#1 something different to do')  # item update

        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 something different to do')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_todos(self):

        Done(engine=my_engine).execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')

        Done(engine=my_engine).execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')

        Done(engine=my_engine).execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')

        c = Todos(engine=my_engine)

        self.assertEqual(c.keyword, 'todos')
        self.assertEqual(c.information_message,
                         u'List items to do')
        self.assertFalse(c.is_hidden)

        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'On the todo list:\n'
                         + u'- #1 formulate scenarios\n'
                         + u'- #2 select the most appropriate scenario')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        c.execute(my_bot, arguments='whatever')
        self.assertEqual(my_engine.mouth.get().text,
                         u'On the todo list:\n'
                         + u'- #1 formulate scenarios\n'
                         + u'- #2 select the most appropriate scenario')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

    def test_steps_lifecycle(self):

        n = Next(engine=my_engine)
        d = Done(engine=my_engine)

        n.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Coming next: write down the driving question')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        d.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        n.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        d.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        n.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                        u'Coming next: identify information gaps and document assumptions')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        d.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        n.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Coming next: formulate scenarios')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        d.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        n.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Coming next: select the most appropriate scenario')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        d.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        n.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()

        d.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text,
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
