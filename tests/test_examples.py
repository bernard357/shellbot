#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot
from examples.steps import Steps, Next, State


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


class ExampleTests(unittest.TestCase):

    def test_steps_steps(self):

        context = Context(settings=my_settings)
        steps = Steps(context, check=True)

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

    def test_steps_state(self):

        context = Context(settings=my_settings)
        bot = ShellBot(context=context)

        steps = Steps(context, check=True)
        s = State(bot=bot, steps=steps)

        self.assertEqual(s.keyword, 'state')
        self.assertEqual(s.information_message,
                         'Display process current state.')
        self.assertTrue(s.is_interactive)
        self.assertFalse(s.is_hidden)
        self.assertTrue(s.steps is not None)

        s.execute()

        self.assertEqual(bot.mouth.get(), u'Current state is undefined')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

    def test_steps_next(self):

        context = Context(settings=my_settings)
        bot = ShellBot(context=context)

        steps = Steps(context, check=True)
        n = Next(bot=bot, steps=steps)

        self.assertEqual(n.keyword, 'next')
        self.assertEqual(n.information_message, u'Move process to next state.')
        self.assertTrue(n.is_interactive)
        self.assertFalse(n.is_hidden)
        self.assertTrue(n.steps is not None)

        n.execute()

        self.assertEqual(bot.mouth.get(),
                         u'New state: Level 1 - '
                         + u'Initial capture of information')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

    def test_steps_lifecycle(self):

        context = Context(settings=my_settings)
        bot = ShellBot(context=context)

        steps = Steps(context, check=True)
        s = State(bot=bot, steps=steps)
        n = Next(bot=bot, steps=steps)

        s.execute()
        self.assertEqual(bot.mouth.get(), u'Current state is undefined')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(bot.mouth.get(),
                         u'New state: Level 1 - '
                         + u'Initial capture of information')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(bot.mouth.get(),
                         u'Current state: Level 1 - '
                         + u'Initial capture of information')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(bot.mouth.get(),
                         u'New state: Level 2 - '
                         + u'Escalation to technical experts')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(bot.mouth.get(),
                         u'Current state: Level 2 - '
                         + u'Escalation to technical experts')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(bot.mouth.get(),
                         u'New state: Level 3 - '
                         + u'Escalation to decision stakeholders')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(bot.mouth.get(),
                         u'Current state: Level 3 - '
                         + u'Escalation to decision stakeholders')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(bot.mouth.get(),
                         u'New state: Terminated - '
                         + u'Process is closed, yet conversation can continue')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        s.execute()
        self.assertEqual(bot.mouth.get(),
                         u'Current state: Terminated - '
                         + u'Process is closed, yet conversation can continue')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

        n.execute()
        self.assertEqual(bot.mouth.get(),
                         u'Current state: Terminated - '
                         + u'Process is closed, yet conversation can continue')
        with self.assertRaises(Exception):
            bot.mouth.get_nowait()

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
