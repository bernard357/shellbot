#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, SpaceFactory
from examples.steps import StepsFactory, Steps, Next, State


my_settings = {

    'process.steps': [

        {
            'label': u'Level 1',
            'message': u'Initial capture of information',
        },

        {
            'label': u'Level 2',
            'message': u'Escalation to technical experts',
            'moderators': 'alice@acme.com',
        },

        {
            'label': u'Level 3',
            'message': u'Escalation to decision stakeholders',
            'participants': 'bob@acme.com',
        },

        {
            'label': u'Terminated',
            'message': u'Process is closed, yet conversation can continue',
        },

    ],

}

my_context = Context(settings=my_settings)
my_bot = ShellBot(context=my_context,
                  mouth=Queue(),
                  space=SpaceFactory.get('local'))


class StepsTests(unittest.TestCase):

    def test_commands(self):

        commands = StepsFactory.commands()
        self.assertTrue(len(commands) == 2)
        for command in commands:
            self.assertTrue(command.keyword in ['next', 'state'])
            self.assertTrue(len(command.information_message) > 1)

    def test_steps(self):

        steps = Steps(context=my_context, configure=True)

        step = steps.step
        self.assertTrue(step is None)

        step = steps.next()
        self.assertEqual(step.label, 'Level 1')
        self.assertEqual(step.label, steps.step.label)
        self.assertEqual(step.message, u'Initial capture of information')
        self.assertEqual(step.markdown, None)
        self.assertEqual(step.moderators, [])
        self.assertEqual(step.participants, [])

        step = steps.next()
        self.assertEqual(step.label, 'Level 2')
        self.assertEqual(step.label, steps.step.label)
        self.assertEqual(step.message, u'Escalation to technical experts')
        self.assertEqual(step.markdown, None)
        self.assertEqual(step.moderators, ['alice@acme.com'])
        self.assertEqual(step.participants, [])

        step = steps.next()
        self.assertEqual(step.label, 'Level 3')
        self.assertEqual(step.label, steps.step.label)

        step = steps.next()
        self.assertEqual(step.label, 'Terminated')
        self.assertEqual(step.label, steps.step.label)

        step = steps.next()
        self.assertEqual(step.label, 'Terminated')
        self.assertEqual(step.label, steps.step.label)

    def test_state(self):

        steps = Steps(context=my_context, configure=True)
        my_bot.steps = steps
        s = State(bot=my_bot)

        self.assertEqual(s.keyword, 'state')
        self.assertEqual(s.information_message,
                         u'Display current state in process')
        self.assertTrue(s.is_interactive)
        self.assertFalse(s.is_hidden)

        s.execute()

        self.assertEqual(my_bot.mouth.get().text, u'Current state is undefined')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_next(self):

        steps = Steps(context=my_context, configure=True)
        my_bot.steps = steps
        n = Next(bot=my_bot)

        self.assertEqual(n.keyword, 'next')
        self.assertEqual(n.information_message, u'Move process to next state')
        self.assertTrue(n.is_interactive)
        self.assertFalse(n.is_hidden)

        n.execute()

        self.assertEqual(my_bot.mouth.get().text,
                         u'New state: Level 1 - '
                         + u'Initial capture of information')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

    def test_lifecycle(self):

        steps = Steps(context=my_context, configure=True)
        my_bot.steps = steps
        s = State(bot=my_bot)
        n = Next(bot=my_bot)

        s.execute()
        self.assertEqual(my_bot.mouth.get().text, u'Current state is undefined')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'New state: Level 1 - '
                         + u'Initial capture of information')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'Current state: Level 1 - '
                         + u'Initial capture of information')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'New state: Level 2 - '
                         + u'Escalation to technical experts')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'Current state: Level 2 - '
                         + u'Escalation to technical experts')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'New state: Level 3 - '
                         + u'Escalation to decision stakeholders')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'Current state: Level 3 - '
                         + u'Escalation to decision stakeholders')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'New state: Terminated - '
                         + u'Process is closed, yet conversation can continue')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'Current state: Terminated - '
                         + u'Process is closed, yet conversation can continue')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(my_bot.mouth.get().text,
                         u'Current state: Terminated - '
                         + u'Process is closed, yet conversation can continue')
        with self.assertRaises(Exception):
            my_bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
