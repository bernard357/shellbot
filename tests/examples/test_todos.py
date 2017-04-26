#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, SpaceFactory
from examples.todos import TodoStore, Done, Drop, History, Next, Todo, Todos


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
my_bot = ShellBot(context=my_context,
                  mouth=Queue(),
                  space=SpaceFactory.get('local'))
my_store = TodoStore(my_bot.context.get('todos.items', []))


class TodosTests(unittest.TestCase):

    def setUp(self):
        my_store.items = my_bot.context.get('todos.items', [])
        my_store.archive = []

    def test_done(self):

        c = Done(bot=my_bot, store=my_store)

        self.assertEqual(c.keyword, 'done')
        self.assertEqual(c.information_message,
                         u'Archive an item from the todo list')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()

        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='#2')

        self.assertEqual(my_bot.mouth.get(),
                         u'#2 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='#2222')

        self.assertEqual(my_bot.mouth.get(),
                         u'usage: done [#<n>]')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='nonsense')

        self.assertEqual(my_bot.mouth.get(),
                         u'usage: done [#<n>]')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_drop(self):

        c = Drop(bot=my_bot, store=my_store)

        self.assertEqual(c.keyword, 'drop')
        self.assertEqual(c.information_message,
                         u'Delete an item from the todo list')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()

        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been deleted')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='#2')

        self.assertEqual(my_bot.mouth.get(),
                         u'#2 has been deleted')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='#2222')

        self.assertEqual(my_bot.mouth.get(),
                         u'usage: drop [#<n>]')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='nonsense')

        self.assertEqual(my_bot.mouth.get(),
                         u'usage: drop [#<n>]')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_history(self):

        Done(bot=my_bot, store=my_store).execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')

        Done(bot=my_bot, store=my_store).execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')

        c = History(bot=my_bot, store=my_store)

        self.assertEqual(c.keyword, 'history')
        self.assertEqual(c.information_message,
                         u'List archived items')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'Items that have been archived:\n'
                         + u'- write down the driving question\n'
                         + u'- gather facts and related information')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='whatever')
        self.assertEqual(my_bot.mouth.get(),
                         u'Items that have been archived:\n'
                         + u'- write down the driving question\n'
                         + u'- gather facts and related information')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_next(self):

        c = Next(bot=my_bot, store=my_store)

        self.assertEqual(c.keyword, 'next')
        self.assertEqual(c.information_message,
                         u'Display next item to do')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()

        self.assertEqual(my_bot.mouth.get(),
                         u'#1 write down the driving question')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='whatever')

        self.assertEqual(my_bot.mouth.get(),
                         u'#1 write down the driving question')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_todo(self):

        my_store.items = []

        c = Todo(bot=my_bot, store=my_store)

        self.assertEqual(c.keyword, 'todo')
        self.assertEqual(c.information_message,
                         u'Append an item to the todo list, or change it')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()  # no argument

        self.assertEqual(my_bot.mouth.get(),
                         u'usage: todo [#n] <something to do>')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='#2 something to do')  # target does not exist

        self.assertEqual(my_bot.mouth.get(),
                         u'usage: todo [#n] <something to do>')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='something to do')  # item creation

        self.assertEqual(my_bot.mouth.get(),
                         u'#1 something to do')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='#1 something different to do')  # item update

        self.assertEqual(my_bot.mouth.get(),
                         u'#1 something different to do')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_todos(self):

        Done(bot=my_bot, store=my_store).execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')

        Done(bot=my_bot, store=my_store).execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')

        Done(bot=my_bot, store=my_store).execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')

        c = Todos(bot=my_bot, store=my_store)

        self.assertEqual(c.keyword, 'todos')
        self.assertEqual(c.information_message,
                         u'List items to do')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'On the todo list:\n'
                         + u'- #1 formulate scenarios\n'
                         + u'- #2 select the most appropriate scenario')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        c.execute(arguments='whatever')
        self.assertEqual(my_bot.mouth.get(),
                         u'On the todo list:\n'
                         + u'- #1 formulate scenarios\n'
                         + u'- #2 select the most appropriate scenario')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_steps_lifecycle(self):

        n = Next(bot=my_bot, store=my_store)
        d = Done(bot=my_bot, store=my_store)

        n.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 write down the driving question')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        d.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 gather facts and related information')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        d.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 identify information gaps and document assumptions')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        d.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 formulate scenarios')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        d.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 select the most appropriate scenario')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        d.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'#1 has been archived')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        d.execute()
        self.assertEqual(my_bot.mouth.get(),
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
