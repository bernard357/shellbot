#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot
from shellbot.machines import Machine, State, Transition


my_bot = ShellBot()


class Helper(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def increment_x(self):
        self.x += 1

    def x_at_least_two(self):
        return self.x >= 2

    def x_is_five(self):
        return self.x == 5

    def increment_y(self):
        self.y += 5

    def increment_z(self):
        self.z += 10


class MachineTests(unittest.TestCase):

    def test_init(self):

        machine = Machine(bot=my_bot)
        self.assertEqual(machine.bot, my_bot)

        machine = Machine(bot=my_bot, weird='w')
        with self.assertRaises(AttributeError):
            print(machine.weird)

        class MyMachine(Machine):
            def on_init(self, weird=None, **kwargs):
                self.weird = weird

        machine = MyMachine(bot=my_bot, weird='w')
        self.assertEqual(machine.weird, 'w')

    def test_build(self):

        machine = Machine(bot=my_bot)

        states = ['one', 'two', 'three']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'one'},
        ]
        machine.build(states=states,
                      transitions=transitions,
                      initial='one')

        self.assertEqual(sorted(machine._states.keys()), ['one', 'three', 'two'])

        self.assertEqual(sorted(machine._transitions.keys()), ['one', 'three', 'two'])

        self.assertEqual(str(machine.state), 'one')

        states = ['one']
        transitions = [
            {'source': 'one'},
        ]
        with self.assertRaises(ValueError):
            machine.build(states=states, transitions=transitions, initial='one')

        states = ['one']
        transitions = [
            {'target': 'one'},
        ]
        with self.assertRaises(ValueError):
            machine.build(states=states, transitions=transitions, initial='one')

        states = ['one']
        transitions = [
            {'source': 'one', 'target': '*weird'},
        ]
        with self.assertRaises(ValueError):
            machine.build(states=states, transitions=transitions, initial='one')

        states = ['one']
        transitions = [
            {'source': '*weird', 'target': 'one'},
        ]
        with self.assertRaises(ValueError):
            machine.build(states=states, transitions=transitions, initial='one')

        states = ['one', 'two', 'three']
        transitions = []
        with self.assertRaises(ValueError):
            machine.build(states=states, transitions=transitions, initial='*weird')

    def test_step(self):

        machine = Machine(bot=my_bot)
        with self.assertRaises(AttributeError):
            machine.step()

    def test_simple_chain(self):
        """Test most basic transition chain."""

        states = ['one', 'two', 'three']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'one'},
        ]

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one')
        self.assertEqual(str(machine.state), 'one')
        machine.step()
        self.assertEqual(str(machine.state), 'two')
        machine.step()
        self.assertEqual(str(machine.state), 'three')
        machine.step()
        self.assertEqual(str(machine.state), 'one')

    def test_simple_during(self):
        """Tests a simple action being performed while in a state."""

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]
        during = {
            'one': helper.increment_x
        }

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          during=during)

        self.assertTrue(helper.x == 0)
        machine.step()
        self.assertTrue(helper.x == 1)
        machine.step()
        self.assertTrue(helper.x == 1)
        machine.step()
        self.assertTrue(helper.x == 2)
        machine.step()
        self.assertTrue(helper.x == 2)

    def test_simple_on_enter(self):
        """Tests a simple action being performed while entering a state."""

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]
        on_enter = {
            'one': helper.increment_x
        }

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          on_enter=on_enter)

        self.assertTrue(helper.x == 0)
        machine.step()
        self.assertTrue(helper.x == 0)
        machine.step()
        self.assertTrue(helper.x == 1)
        machine.step()
        self.assertTrue(helper.x == 1)
        machine.step()
        self.assertTrue(helper.x == 2)

    def test_simple_on_exit(self):
        """Tests a simple action being performed while exiting a state."""

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]
        on_exit = {
            'one': helper.increment_x
        }

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          on_exit=on_exit)

        self.assertTrue(helper.x == 0)
        machine.step()
        self.assertTrue(helper.x == 1)
        machine.step()
        self.assertTrue(helper.x == 1)
        machine.step()
        self.assertTrue(helper.x == 2)
        machine.step()
        self.assertTrue(helper.x == 2)

    def test_simple_condition(self):
        """Tests a simple condition check before transitioning."""

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two', 'condition': helper.x_is_five},
            {'source': 'two', 'target': 'one'},
        ]
        during = {
            'one': helper.increment_x
        }

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          during=during)

        for x in range(5):
            self.assertTrue(helper.x == x)
            self.assertTrue(str(machine.state) == 'one')
            machine.step()
        self.assertTrue(helper.x == 5)
        self.assertTrue(str(machine.state) == 'two')
        machine.step()
        self.assertTrue(helper.x == 5)
        self.assertTrue(str(machine.state) == 'one')
        machine.step()
        self.assertTrue(helper.x == 6)
        self.assertTrue(str(machine.state) == 'one')
        machine.step()
        self.assertTrue(helper.x == 7)
        self.assertTrue(str(machine.state) == 'one')

    def test_simple_action(self):
        """Tests a simple action while transitioning."""

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two', 'action': helper.increment_x},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one')

        self.assertTrue(helper.x == 0)
        self.assertTrue(str(machine.state) == 'one')
        machine.step()
        self.assertTrue(helper.x == 1)
        self.assertTrue(str(machine.state) == 'two')
        machine.step()
        self.assertTrue(helper.x == 1)
        self.assertTrue(str(machine.state) == 'one')
        machine.step()
        self.assertTrue(helper.x == 2)
        self.assertTrue(str(machine.state) == 'two')

    def test_composite(self):
        """Tests that things happen without interference."""

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two', 'condition': helper.x_at_least_two},
            {'source': 'two', 'target': 'one'},
        ]
        during = {
            'one': helper.increment_x
        }
        on_enter = {
            'one': helper.increment_y
        }
        on_exit = {
            'one': helper.increment_z
        }

        machine = Machine(bot=my_bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          during=during,
                          on_enter=on_enter,
                          on_exit=on_exit)

        machine.step()
        self.assertTrue(helper.x == 1)
        self.assertTrue(helper.y == 0)
        self.assertTrue(helper.z == 0)
        self.assertTrue(str(machine.state) == 'one')
        machine.step()
        self.assertTrue(helper.x == 2)
        self.assertTrue(helper.y == 0)
        self.assertTrue(helper.z == 10)
        self.assertTrue(str(machine.state) == 'two')
        machine.step()
        self.assertTrue(helper.x == 2)
        self.assertTrue(helper.y == 5)
        self.assertTrue(helper.z == 10)
        self.assertTrue(str(machine.state) == 'one')


class StateTests(unittest.TestCase):

    def test_init(self):

        state = State(name='a state')
        self.assertEqual(state.name, 'a state')
        self.assertTrue(state._during is None)
        self.assertTrue(state._on_enter is None)
        self.assertTrue(state._on_exit is None)

    def test_repr(self):

        state = State(name='a state')
        self.assertEqual(state.__repr__(), u'State(a state, None, None, None)')

    def test_str(self):

        state = State(name='a state')
        self.assertEqual(str(state), 'a state')

    def test_during(self):

        state = State(name='a state')
        state.during()

        state = State(name='a state', during=mock.Mock())
        state.during()
        self.assertTrue(state._during.called)

    def test_on_enter(self):

        state = State(name='a state')
        state.on_enter()

        state = State(name='a state', on_enter=mock.Mock())
        state.on_enter()
        self.assertTrue(state._on_enter.called)

    def test_on_exit(self):

        state = State(name='a state')
        state.on_exit()

        state = State(name='a state', on_exit=mock.Mock())
        state.on_exit()
        self.assertTrue(state._on_exit.called)


class TransitionTests(unittest.TestCase):

    def test_init(self):

        begin = State(name='begin')
        end = State(name='end')
        transition = Transition(source=begin, target=end)
        self.assertEqual(transition.source, begin)
        self.assertEqual(transition.target, end)
        self.assertTrue(transition._condition is None)
        self.assertTrue(transition._action is None)

    def test_repr(self):

        begin = State(name='begin')
        end = State(name='end')
        transition = Transition(source=begin, target=end)
        self.assertEqual(transition.__repr__(),
                         u'Transition(State(begin, None, None, None), State(end, None, None, None), None, None)')

    def test_str(self):

        begin = State(name='begin')
        end = State(name='end')
        transition = Transition(source=begin, target=end)
        self.assertEqual(str(transition), 'begin => end')

    def test_condition(self):

        begin = State(name='begin')
        end = State(name='end')

        transition = Transition(source=begin, target=end)
        self.assertTrue(transition.condition())

        transition = Transition(source=begin, target=end, condition=lambda:True)
        self.assertTrue(transition.condition())

        transition = Transition(source=begin, target=end, condition=lambda:False)
        self.assertFalse(transition.condition())

    def test_action(self):

        begin = State(name='begin')
        end = State(name='end')

        transition = Transition(source=begin, target=end)
        transition.action()

        transition = Transition(source=begin, target=end, action=mock.Mock())
        transition.action()
        self.assertTrue(transition._action.called)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
