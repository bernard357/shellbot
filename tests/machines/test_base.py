#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
from threading import Timer
import time

from shellbot import Context, Engine, ShellBot, Bus
from shellbot.machines import Machine, State, Transition


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

    def extended(self, extra=None, **kwargs):
        self.extra = extra

    def input_is_big(self, gauge=0, **kwargs):
        return gauge > 23


class MachineTests(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()
        self.engine.bus = Bus(self.engine.context)
        self.engine.bus.check()
        self.engine.publisher = self.engine.bus.publish()
        self.bot = ShellBot(engine=self.engine)
        self.bot.subscriber = self.engine.bus.subscribe('*id')
        self.bot.publisher = self.engine.publisher

    def tearDown(self):
        del self.bot
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("***** machine/init")

        machine = Machine(bot=self.bot)
        self.assertEqual(machine.bot, self.bot)

        machine = Machine(bot=self.bot, weird='w')
        with self.assertRaises(AttributeError):
            print(machine.weird)

        class MyMachine(Machine):
            def on_init(self, extra=None, **kwargs):
                self.extra = extra

        machine = MyMachine(bot=self.bot, extra='w')
        self.assertEqual(machine.extra, 'w')

    def test_getter(self):

        logging.info("***** machine/getter")

        machine = Machine(bot=self.bot)

        # undefined key
        self.assertEqual(machine.get('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(machine.get('hello', whatever), whatever)

        # set the key
        machine.set('hello', 'world')
        self.assertEqual(machine.get('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(machine.get('hello', 'whatever'), 'world')

        # except when set to None
        machine.set('special', None)
        self.assertEqual(machine.get('special', []), [])

    def test_build(self):

        logging.info("***** machine/build")

        machine = Machine(bot=self.bot)

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

        self.assertEqual(machine.current_state.name, 'one')

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

    def test_state(self):

        logging.info("***** machine/state")

        machine = Machine(bot=self.bot)

        states = ['one', 'two', 'three']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'one'},
        ]
        machine.build(states=states,
                      transitions=transitions,
                      initial='one')

        self.assertEqual(machine.state('one').name, 'one')
        self.assertEqual(machine.state('two').name, 'two')
        self.assertEqual(machine.state('three').name, 'three')

    def test_current_state(self):

        logging.info("***** machine/current_state")

        machine = Machine(bot=self.bot)

        states = ['one', 'two', 'three']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'one'},
        ]
        machine.build(states=states,
                      transitions=transitions,
                      initial='three')

        self.assertEqual(machine.current_state.name, 'three')

    def test_reset_static(self):
        """Test reset a static machine."""

        logging.info("***** machine/reset a static machine")

        states = ['one', 'two', 'three']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')
        machine.mixer.put(None)
        self.assertFalse(machine.is_running)
        self.assertEqual(machine.current_state.name, 'one')
        machine.step()
        self.assertEqual(machine.current_state.name, 'two')
        machine.reset()
        self.assertEqual(machine.current_state.name, 'one')
        machine.step()
        self.assertEqual(machine.current_state.name, 'two')

    def test_reset_dynamic(self):
        """Test reset a dynamic machine."""

        logging.info("***** machine/reset a dynamic machine")

        machine = Machine(bot=self.bot)

        states = ['one', 'two', 'three', 'four']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three', 'condition': lambda **z: machine.get('go_ahead', False) },
        ]
        on_enter = { 'three': machine.stop }
        machine.build(states=states,
                      transitions=transitions,
                      initial='one',
                      on_enter=on_enter)

        self.engine.set('general.switch', 'on')
        machine_process = machine.start(tick=0.001)
        while machine.current_state.name != 'two':
            time.sleep(0.01)
        self.assertTrue(machine.is_running)
        machine.reset()
        self.assertEqual(machine.current_state.name, 'two')
        machine.set('go_ahead', True)
        machine_process.join()
        self.assertEqual(machine.current_state.name, 'three')
        self.assertFalse(machine.is_running)
        machine.reset()
        self.assertEqual(machine.current_state.name, 'one')

    def test_step(self):

        logging.info("***** machine/step")

        machine = Machine(bot=self.bot)
        with self.assertRaises(AttributeError):
            machine.step()

    def test_simple_chain(self):
        """Test most basic transition chain."""

        logging.info("***** machine/simple chain")

        states = ['one', 'two', 'three']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')
        self.assertEqual(machine.current_state.name, 'one')
        machine.step()
        self.assertEqual(machine.current_state.name, 'two')
        machine.step()
        self.assertEqual(machine.current_state.name, 'three')
        machine.step()
        self.assertEqual(machine.current_state.name, 'one')

    def test_simple_during(self):
        """Tests a simple action being performed while in a state."""

        logging.info("***** machine/simple during")

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]
        during = {
            'one': helper.increment_x
        }

        machine = Machine(bot=self.bot,
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

    def test_extra_during(self):
        """Tests an extended action being performed while in a state."""

        logging.info("***** machine/extra during")

        helper = Helper()
        states = ['one']
        transitions = [
            {'source': 'one', 'target': 'one'},
        ]
        during = {
            'one': helper.extended
        }

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          during=during)

        machine.step()
        self.assertTrue(helper.extra is None)
        machine.step(extra=123)
        self.assertTrue(helper.extra == 123)

    def test_simple_on_enter(self):
        """Tests a simple action being performed while entering a state."""

        logging.info("***** machine/simple on_enter")

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]
        on_enter = {
            'one': helper.increment_x
        }

        machine = Machine(bot=self.bot,
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

        logging.info("***** machine/simple on_exit")

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]
        on_exit = {
            'one': helper.increment_x
        }

        machine = Machine(bot=self.bot,
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

        logging.info("***** machine/simple condition")

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two', 'condition': helper.x_is_five},
            {'source': 'two', 'target': 'one'},
        ]
        during = {
            'one': helper.increment_x
        }

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one',
                          during=during)

        for x in range(5):
            self.assertTrue(helper.x == x)
            self.assertTrue(machine.current_state.name == 'one')
            machine.step()
        self.assertTrue(helper.x == 5)
        self.assertTrue(machine.current_state.name == 'two')
        machine.step()
        self.assertTrue(helper.x == 5)
        self.assertTrue(machine.current_state.name == 'one')
        machine.step()
        self.assertTrue(helper.x == 6)
        self.assertTrue(machine.current_state.name == 'one')
        machine.step()
        self.assertTrue(helper.x == 7)
        self.assertTrue(machine.current_state.name == 'one')

    def test_extra_condition(self):
        """Tests an extended condition check before transitioning."""

        logging.info("***** machine/extra condition")

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two', 'condition': helper.input_is_big},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')

        self.assertTrue(machine.current_state.name == 'one')
        machine.step()
        self.assertTrue(machine.current_state.name == 'one')
        machine.step(gauge=5)
        self.assertTrue(machine.current_state.name == 'one')
        machine.step(gauge=50)
        self.assertTrue(machine.current_state.name == 'two')

    def test_simple_action(self):
        """Tests a simple action while transitioning."""

        logging.info("***** machine/simple action")

        helper = Helper()
        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two', 'action': helper.increment_x},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')

        self.assertTrue(helper.x == 0)
        self.assertTrue(machine.current_state.name == 'one')
        machine.step()
        self.assertTrue(helper.x == 1)
        self.assertTrue(machine.current_state.name == 'two')
        machine.step()
        self.assertTrue(helper.x == 1)
        self.assertTrue(machine.current_state.name == 'one')
        machine.step()
        self.assertTrue(helper.x == 2)
        self.assertTrue(machine.current_state.name == 'two')

    def test_composite(self):
        """Tests that things happen without interference."""

        logging.info("***** machine/composite")

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

        machine = Machine(bot=self.bot,
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
        self.assertTrue(machine.current_state.name == 'one')
        machine.step()
        self.assertTrue(helper.x == 2)
        self.assertTrue(helper.y == 0)
        self.assertTrue(helper.z == 10)
        self.assertTrue(machine.current_state.name == 'two')
        machine.step()
        self.assertTrue(helper.x == 2)
        self.assertTrue(helper.y == 5)
        self.assertTrue(helper.z == 10)
        self.assertTrue(machine.current_state.name == 'one')

    def test_start(self):
        """Infinite loop stopped via general switch"""

        logging.info("***** machine/start")

        states = ['one', 'two', 'three', 'four']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'four'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')

        self.engine.set('general.switch', 'on')
        machine_process = machine.start(tick=0.001)
        machine.step()
        time.sleep(0.05)
        self.engine.set('general.switch', 'off')
        machine_process.join()

        self.assertTrue(machine.current_state.name != 'one')

    def test_restart(self):

        logging.info("***** machine/restart")

        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                            states=states,
                            transitions=transitions,
                            initial='one')

        self.engine.set('general.switch', 'on')
        machine.start(tick=0.001)

        while not machine.is_running:  # ensure it is running
            time.sleep(0.001)

        self.assertFalse(machine.restart())

        machine.mixer.put(None)

        while machine.is_running:  # ensure it is stopped
            time.sleep(0.001)

        self.assertTrue(machine.restart())

        while not machine.is_running:  # ensure it is running
            time.sleep(0.001)

        machine.mixer.put(None)

        while machine.is_running:  # ensure it is stopped
            time.sleep(0.001)

    def test_stop(self):
        """Machine is stopped after a while"""

        logging.info("***** machine/stop")

        states = ['one', 'two', 'three', 'four']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'four'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')

        self.engine.set('general.switch', 'on')
        machine_process = machine.start(tick=0.001)
        machine.stop()
        machine_process.join()

    def test_lifecycle(self):
        """Machine stops itself on last transition"""

        logging.info("***** machine/lifecycle")

        machine = Machine(bot=self.bot)

        states = ['one', 'two', 'three', 'four']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'three'},
            {'source': 'three', 'target': 'four'},
        ]
        on_enter = { 'four': machine.stop }
        machine.build(states=states,
                      transitions=transitions,
                      initial='one',
                      on_enter=on_enter)

        self.engine.set('general.switch', 'on')
        machine_process = machine.start(tick=0.001)
        machine_process.join()

        self.assertEqual(machine.current_state.name, 'four')

    def test_run(self):

        logging.info("***** machine/run")

        class MyMachine(Machine):

            def execute(self, arguments=None, **kwargs):
                if arguments == 'ctl-c':
                    raise KeyboardInterrupt()
                raise Exception('TEST')

        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]

        machine = MyMachine(bot=self.bot,
                            states=states,
                            transitions=transitions,
                            initial='one')

        machine.on_start = mock.Mock()
        machine.on_stop = mock.Mock()
        self.engine.set('general.switch', 'off')

        logging.debug(u"- general switch is off")
        machine.run()

        machine.on_start.assert_called_with()
        machine.on_stop.assert_called_with()

        self.engine.set('general.switch', 'on')

        machine.TICK_DURATION = 0.003
        t = Timer(0.004, machine.stop)
        t.start()

        logging.debug(u"- poison pill on delay")
        machine.run()

        machine.mixer.put(None)

        logging.debug(u"- exit on poison pill")
        machine.run()

        machine.mixer.put('exception')

        logging.debug(u"- break on exception")
        machine.run()

        machine.mixer.put('ctl-c')

        logging.debug(u"- break on KeyboardInterrupt")
        machine.run()

    def test_on_start(self):

        logging.info("***** machine/on_start")

        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                            states=states,
                            transitions=transitions,
                            initial='one')

        machine.on_start()

        machine.on_start = mock.Mock()
        self.engine.set('general.switch', 'on')
        machine.start(tick=0.001)

        machine.on_start.ssert_called_with()

        machine.stop()

    def test_on_stop(self):

        logging.info("***** machine/on_stop")

        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                            states=states,
                            transitions=transitions,
                            initial='one')

        machine.on_stop()

        machine.on_stop = mock.Mock()
        self.engine.set('general.switch', 'on')
        machine.start(tick=0.001)
        machine.stop()
        machine.on_stop.ssert_called_with()

    def test_execute(self):

        logging.info("***** machine/execute")

        states = ['one', 'two']
        transitions = [
            {'source': 'one', 'target': 'two'},
            {'source': 'two', 'target': 'one'},
        ]

        machine = Machine(bot=self.bot,
                          states=states,
                          transitions=transitions,
                          initial='one')

        machine.step = mock.Mock()
        machine.execute('ping pong')
        machine.step.assert_called_with(arguments='ping pong', event='input')


class StateTests(unittest.TestCase):

    def test_init(self):

        logging.info("***** state/init")

        state = State(name='a state')
        self.assertEqual(state.name, 'a state')
        self.assertTrue(state._during is None)
        self.assertTrue(state._on_enter is None)
        self.assertTrue(state._on_exit is None)

    def test_repr(self):

        logging.info("***** state/repr")

        state = State(name='a state')
        self.assertEqual(state.__repr__(), u'State(a state, None, None, None)')

    def test_str(self):

        logging.info("***** state/str")

        state = State(name='a state')
        self.assertEqual(str(state), 'a state')

    def test_during(self):

        logging.info("***** state/during")

        state = State(name='a state')
        state.during()

        state = State(name='a state', during=mock.Mock())
        state.during()
        self.assertTrue(state._during.called)

        state = State(name='a state', during=mock.Mock())
        state.during(extra=123)
        state._during.assert_called_with(extra=123)

    def test_on_enter(self):

        logging.info("***** state/on_enter")

        state = State(name='a state')
        state.on_enter()

        state = State(name='a state', on_enter=mock.Mock())
        state.on_enter()
        self.assertTrue(state._on_enter.called)

    def test_on_exit(self):

        logging.info("***** state/on_exit")

        state = State(name='a state')
        state.on_exit()

        state = State(name='a state', on_exit=mock.Mock())
        state.on_exit()
        self.assertTrue(state._on_exit.called)


class TransitionTests(unittest.TestCase):

    def test_init(self):

        logging.info("***** transition/init")

        begin = State(name='begin')
        end = State(name='end')
        transition = Transition(source=begin, target=end)
        self.assertEqual(transition.source, begin)
        self.assertEqual(transition.target, end)
        self.assertTrue(transition._condition is None)
        self.assertTrue(transition._action is None)

    def test_repr(self):

        logging.info("***** transition/repr")

        begin = State(name='begin')
        end = State(name='end')
        transition = Transition(source=begin, target=end)
        self.assertEqual(transition.__repr__(),
                         u'Transition(State(begin, None, None, None), State(end, None, None, None), None, None)')

    def test_str(self):

        logging.info("***** transition/str")

        begin = State(name='begin')
        end = State(name='end')
        transition = Transition(source=begin, target=end)
        self.assertEqual(str(transition), 'begin => end')

    def test_condition(self):

        logging.info("***** transition/condition")

        begin = State(name='begin')
        end = State(name='end')

        transition = Transition(source=begin, target=end)
        self.assertTrue(transition.condition())

        transition = Transition(source=begin, target=end, condition=lambda:True)
        self.assertTrue(transition.condition())

        transition = Transition(source=begin, target=end, condition=lambda:False)
        self.assertFalse(transition.condition())

        transition = Transition(source=begin, target=end, condition=mock.Mock(return_value=True))
        transition.condition(extra=123)
        transition._condition.assert_called_with(extra=123)

    def test_action(self):

        logging.info("***** transition/action")

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
