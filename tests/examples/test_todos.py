#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, ShellBot, SpaceFactory, Bus
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


class TodosTests(unittest.TestCase):

    def setUp(self):
        self.context = Context(settings=my_settings)
        self.engine = Engine(context=self.context, mouth=Queue())
        self.engine.factory = TodoFactory(self.engine.get('todos.items', []))
        self.engine.bus = Bus(self.context)
        self.engine.bus.check()
        self.engine.publisher = self.engine.bus.publish()
        self.bot = self.engine.get_bot()

    def tearDown(self):
        del self.bot
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_commands(self):

        logging.info(u"**** commands")

        commands = TodoFactory.commands()
        self.assertTrue(len(commands) == 6)
        for command in commands:
            self.assertTrue(command.keyword in ['done', 'drop', 'history', 'next', 'todo', 'todos'])
            self.assertTrue(len(command.information_message) > 1)

    def test_done(self):

        logging.info(u"**** done")

        c = Done(engine=self.engine)

        self.assertEqual(c.keyword, 'done')
        self.assertEqual(c.information_message,
                         u'Archive an item from the todo list')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)

        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: write down the driving question')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='#2')

        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: identify information gaps and document assumptions')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='#2222')

        self.assertEqual(self.engine.mouth.get().text,
                         u'usage: done [#<n>]')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='nonsense')

        self.assertEqual(self.engine.mouth.get().text,
                         u'usage: done [#<n>]')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_drop(self):

        logging.info(u"**** drop")

        c = Drop(engine=self.engine)

        self.assertEqual(c.keyword, 'drop')
        self.assertEqual(c.information_message,
                         u'Delete an item from the todo list')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)

        self.assertEqual(self.engine.mouth.get().text,
                         u'Deleted: write down the driving question')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='#2')

        self.assertEqual(self.engine.mouth.get().text,
                         u'Deleted: identify information gaps and document assumptions')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='#2222')

        self.assertEqual(self.engine.mouth.get().text,
                         u'usage: drop [#<n>]')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='nonsense')

        self.assertEqual(self.engine.mouth.get().text,
                         u'usage: drop [#<n>]')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_history(self):

        logging.info(u"**** history")

        Done(engine=self.engine).execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: write down the driving question')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')

        Done(engine=self.engine).execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: gather facts and related information')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: identify information gaps and document assumptions')

        c = History(engine=self.engine)

        self.assertEqual(c.keyword, 'history')
        self.assertEqual(c.information_message,
                         u'List archived items')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Items that have been archived:\n'
                         + u'- write down the driving question\n'
                         + u'- gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='whatever')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Items that have been archived:\n'
                         + u'- write down the driving question\n'
                         + u'- gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_next(self):

        logging.info(u"**** next")

        c = Next(engine=self.engine)

        self.assertEqual(c.keyword, 'next')
        self.assertEqual(c.information_message,
                         u'Display next item to do')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)

        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: write down the driving question')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='whatever')

        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: write down the driving question')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_todo(self):

        logging.info(u"**** todo")

        self.engine.factory.items = []

        c = Todo(engine=self.engine)

        self.assertEqual(c.keyword, 'todo')
        self.assertEqual(c.information_message,
                         u'Append an item to the todo list, or change it')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)  # no argument

        self.assertEqual(self.engine.mouth.get().text,
                         u'usage: todo [#n] <something to do>')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='#2 something to do')  # target does not exist

        self.assertEqual(self.engine.mouth.get().text,
                         u'usage: todo [#n] <something to do>')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='something to do')  # item creation

        self.assertEqual(self.engine.mouth.get().text,
                         u'#1: something to do')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='#1 something different to do')  # item update

        self.assertEqual(self.engine.mouth.get().text,
                         u'#1: something different to do')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_todos(self):

        logging.info(u"**** todos")

        Done(engine=self.engine).execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: write down the driving question')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')

        Done(engine=self.engine).execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: gather facts and related information')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: identify information gaps and document assumptions')

        Done(engine=self.engine).execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: identify information gaps and document assumptions')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: formulate scenarios')

        c = Todos(engine=self.engine)

        self.assertEqual(c.keyword, 'todos')
        self.assertEqual(c.information_message,
                         u'List items to do')
        self.assertFalse(c.is_hidden)

        c.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'On the todo list:\n'
                         + u'- #1 formulate scenarios\n'
                         + u'- #2 select the most appropriate scenario')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        c.execute(self.bot, arguments='whatever')
        self.assertEqual(self.engine.mouth.get().text,
                         u'On the todo list:\n'
                         + u'- #1 formulate scenarios\n'
                         + u'- #2 select the most appropriate scenario')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

    def test_steps_lifecycle(self):

        logging.info(u"**** life cycle")

        n = Next(engine=self.engine)
        d = Done(engine=self.engine)

        n.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: write down the driving question')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        d.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: write down the driving question')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        n.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: gather facts and related information')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        d.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: gather facts and related information')
        self.assertEqual(self.engine.mouth.get().text,
                        u'Coming next: identify information gaps and document assumptions')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        n.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                        u'Coming next: identify information gaps and document assumptions')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        d.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: identify information gaps and document assumptions')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: formulate scenarios')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        n.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: formulate scenarios')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        d.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: formulate scenarios')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: select the most appropriate scenario')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        n.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Coming next: select the most appropriate scenario')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        d.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Archived: select the most appropriate scenario')
        self.assertEqual(self.engine.mouth.get().text,
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        n.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()

        d.execute(self.bot)
        self.assertEqual(self.engine.mouth.get().text,
                         u'Nothing to do yet.')
        with self.assertRaises(Exception):
            self.engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
