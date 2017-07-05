#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process, Queue
import sys
from threading import Timer
import time

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot
from shellbot.machines.steps import Step, Steps

my_bot = ShellBot()


class FakeMachine(object):

    def __init__(self, running=False):
        self.running = running
        self._reset = False
        self.started = False

    def reset(self):
        self._reset = True

    def start(self):
        self.started = True

    @property
    def is_running(self):
        return self.running


my_raw_steps = [

    {
        'label': u'Level 1',
        'message': u'Initial capture of information',
        'content': u'**Initial** `capture` of _information_',
        'file': "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg",
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

]

my_steps = [

    Step({
        'label': u'Level 1',
        'message': u'Initial capture of information',
        'content': u'**Initial** `capture` of _information_',
        'file': "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg",
    }, 1),

    Step({
        'label': u'Level 2',
        'message': u'Escalation to technical experts',
        'moderators': 'alice@acme.com',
        'machine': FakeMachine(running=False),
    }, 2),

    Step({
        'label': u'Level 3',
        'message': u'Escalation to decision stakeholders',
        'participants': 'bob@acme.com',
        'machine': FakeMachine(running=False),
    }, 3),

    Step({
        'label': u'Terminated',
        'message': u'Process is closed, yet conversation can continue',
        'machine': FakeMachine(running=False),
    }, 4),

]

my_running_steps = [

    Step({
        'label': u'Level 1',
        'message': u'Initial capture of information',
        'content': u'**Initial** `capture` of _information_',
        'file': "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg",
    }, 1),

    Step({
        'label': u'Level 2',
        'message': u'Escalation to technical experts',
        'moderators': 'alice@acme.com',
        'machine': FakeMachine(running=True),
    }, 2),

    Step({
        'label': u'Level 3',
        'message': u'Escalation to decision stakeholders',
        'participants': 'bob@acme.com',
        'machine': FakeMachine(running=True),
    }, 3),

    Step({
        'label': u'Terminated',
        'message': u'Process is closed, yet conversation can continue',
        'machine': FakeMachine(running=True),
    }, 4),

]


class StepsTests(unittest.TestCase):

    def tearDown(self):

        for step in my_steps:
            if step.machine:
                step.machine.started = False
                step.machine.running = False

        for step in my_running_steps:
            if step.machine:
                step.machine.started = False
                step.machine.running = True

        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("******** init")

        machine = Steps(bot=my_bot)
        self.assertEqual(machine.bot, my_bot)
        self.assertEqual(machine.prefix, "steps")
        self.assertEqual(len(machine.steps), 0)

        machine = Steps(bot=my_bot,
                        steps=my_raw_steps)
        self.assertEqual(len(machine.steps), 4)
        for step in machine.steps:
            self.assertTrue(isinstance(step, Step))

        machine = Steps(bot=my_bot,
                        steps=my_steps)
        self.assertEqual(len(machine.steps), 4)
        for step in machine.steps:
            self.assertTrue(isinstance(step, Step))

        machine = Steps(bot=my_bot,
                        steps=my_running_steps)
        self.assertEqual(len(machine.steps), 4)
        for step in machine.steps:
            self.assertTrue(isinstance(step, Step))

    def test_reset(self):

        logging.info("******** reset")

        machine = Steps(bot=my_bot,
                        steps=my_raw_steps)
        self.assertEqual(len(machine.steps), 4)

        self.assertEqual(machine.get('_index'), None)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            machine.next_step()
            self.assertEqual(machine.get('_index'), 0)

            machine.next_step()
            self.assertEqual(machine.get('_index'), 1)

            machine.reset()
            self.assertEqual(machine.get('_index'), None)

            machine.next_step()
            self.assertEqual(machine.get('_index'), 0)

            machine.next_step()
            self.assertEqual(machine.get('_index'), 1)

    def test_current_step(self):

        logging.info("******** current_step")

        machine = Steps(bot=my_bot)
        self.assertEqual(machine.current_step, None)

        machine = Steps(bot=my_bot,
                        steps=my_steps)

        self.assertEqual(machine.current_step, None)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            machine.next_step()
            self.assertEqual(machine.current_step, my_steps[0])

            sub_machine = machine.current_step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            machine.next_step()
            self.assertEqual(machine.current_step, my_steps[1])

            sub_machine = machine.current_step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            machine.next_step()
            self.assertEqual(machine.current_step, my_steps[2])

            sub_machine = machine.current_step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            machine.next_step()
            self.assertEqual(machine.current_step, my_steps[3])

            sub_machine = machine.current_step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            machine.next_step()
            self.assertEqual(machine.current_step, my_steps[3])

            sub_machine = machine.current_step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            machine.next_step()
            self.assertEqual(machine.current_step, my_steps[3])

            sub_machine = machine.current_step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

    def test_next_step(self):

        logging.info("******** next_step")

        machine = Steps(bot=my_bot)
        step = machine.next_step()
        self.assertEqual(step, None)

        machine = Steps(bot=my_bot,
                        steps=my_steps)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            step = machine.next_step()
            self.assertEqual(step, my_steps[0])

            sub_machine = step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            step = machine.next_step()
            self.assertEqual(step, my_steps[1])

            sub_machine = step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            step = machine.next_step()
            self.assertEqual(step, my_steps[2])

            sub_machine = step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            step = machine.next_step()
            self.assertEqual(step, my_steps[3])

            sub_machine = step.machine
            if sub_machine:
                self.assertTrue(sub_machine.started)
                self.assertTrue(sub_machine._reset)

            step = machine.next_step()
            self.assertEqual(step, None)

            step = machine.next_step()
            self.assertEqual(step, None)

    def test_step_has_completed(self):

        logging.info("******** step_has_completed")

        machine = Steps(bot=my_bot)
        self.assertTrue(machine.step_has_completed())

        machine = Steps(bot=my_bot,
                        steps=my_steps)

        self.assertTrue(machine.step_has_completed())

        with mock.patch.object(my_bot,
                               'space') as mocked:

            machine.next_step()
            self.assertTrue(machine.step_has_completed())

            machine.next_step()
            self.assertTrue(machine.step_has_completed())

            step = machine.next_step()
            self.assertTrue(machine.step_has_completed())

            machine.next_step()
            self.assertTrue(machine.step_has_completed())

        machine = Steps(bot=my_bot,
                        steps=my_running_steps)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            machine.next_step()
            self.assertTrue(machine.step_has_completed())

            step = machine.next_step()
            self.assertFalse(machine.step_has_completed())
            step.machine.running = False
            self.assertTrue(machine.step_has_completed())

            step = machine.next_step()
            self.assertFalse(machine.step_has_completed())
            step.machine.running = False
            self.assertTrue(machine.step_has_completed())

            step = machine.next_step()
            self.assertFalse(machine.step_has_completed())
            step.machine.running = False
            self.assertTrue(machine.step_has_completed())

    def test_if_ready(self):

        logging.info("******** if_ready")

        machine = Steps(bot=my_bot,
                        steps=my_steps)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            self.assertTrue(machine.if_ready())
            self.assertTrue(machine.if_ready(event='tick'))
            self.assertTrue(machine.if_ready(event='next'))

            machine.step()
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_steps[0])

        class MySteps(Steps):
            def if_ready(self, **kwargs):
                return False

        machine = MySteps(bot=my_bot,
                          steps=my_steps)

        self.assertFalse(machine.if_ready())
        self.assertFalse(machine.if_ready(event='tick'))
        self.assertFalse(machine.if_ready(event='next'))

        self.assertEqual(machine.current_step, None)
        self.assertEqual(machine.mutables['state'], 'begin')

        machine.step()
        self.assertEqual(machine.mutables['state'], 'begin')
        self.assertEqual(machine.current_step, None)

        machine.step(event='tick')
        self.assertEqual(machine.mutables['state'], 'begin')
        self.assertEqual(machine.current_step, None)

        machine.step(event='next')
        self.assertEqual(machine.mutables['state'], 'begin')
        self.assertEqual(machine.current_step, None)

    def test_if_next(self):

        logging.info("******** if_next")

        machine = Steps(bot=my_bot,
                        steps=my_steps)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            self.assertFalse(machine.if_next())
            self.assertFalse(machine.if_next(event='tick'))
            self.assertTrue(machine.if_next(event='next'))

        with mock.patch.object(my_bot,
                               'space') as mocked:

            self.assertEqual(machine.current_step, None)
            self.assertEqual(machine.mutables['state'], 'begin')

            machine.step()
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_steps[0])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[0])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[0])

            machine.step(event='next')
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_steps[1])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[1])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[1])

            machine.step(event='next')
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_steps[2])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[2])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[2])

            machine.step(event='next')
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_steps[3])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_steps[3])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_steps[3])

            machine.step(event='next')
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_steps[3])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_steps[3])

            machine.step(event='tick')
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_steps[3])

        machine = Steps(bot=my_bot,
                        steps=my_running_steps)

        with mock.patch.object(my_bot,
                               'space') as mocked:

            self.assertEqual(machine.current_step, None)
            self.assertEqual(machine.mutables['state'], 'begin')

            machine.step()
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[0])

            machine.step(event='tick') # 1 completed
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_running_steps[0])

            machine.step(event='tick') # 1 completed
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_running_steps[0])

            machine.step(event='next') # 2 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[1])

            machine.step(event='tick') # 2 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[1])

            machine.step(event='tick') # 2 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[1])

            machine.step(event='next') # 2 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[1])

            machine.current_step.machine.running = False
            machine.step(event='tick') # 2 completed
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_running_steps[1])

            machine.step(event='next') # 3 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[2])

            machine.step(event='tick') # 3 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[2])

            machine.step(event='tick') # 3 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[2])

            machine.step(event='next') # 3 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[2])

            machine.current_step.machine.running = False
            machine.step(event='tick') # 3 completed
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_running_steps[2])

            machine.step(event='tick') # 3 completed
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_running_steps[2])

            machine.step(event='next') # 4 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.step(event='tick') # 4 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.step(event='tick') # 4 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.step(event='next') # 4 running
            self.assertEqual(machine.mutables['state'], 'running')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.current_step.machine.running = False
            machine.step(event='tick') # 4 completed
            self.assertEqual(machine.mutables['state'], 'completed')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.step(event='tick') # end
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.step(event='next') # end
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_running_steps[3])

            machine.step(event='tick') # end
            self.assertEqual(machine.mutables['state'], 'end')
            self.assertEqual(machine.current_step, my_running_steps[3])

    def test_step_init(self):

        logging.info("******** step.init")

        step = my_steps[0]
        self.assertEqual(step.label, 'Level 1')
        self.assertEqual(step.message, 'Initial capture of information')
        self.assertEqual(step.content, '**Initial** `capture` of _information_')
        self.assertEqual(step.file, 'https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg')
        self.assertEqual(step.moderators, [])
        self.assertEqual(step.participants, [])
        self.assertEqual(step.machine, None)

        step = my_steps[1]
        self.assertEqual(step.label, 'Level 2')
        self.assertEqual(step.message, 'Escalation to technical experts')
        self.assertEqual(step.content, None)
        self.assertEqual(step.file, None)
        self.assertEqual(step.moderators, ['alice@acme.com'])
        self.assertEqual(step.participants, [])
        self.assertTrue(step.machine is not None)

        step = my_steps[2]
        self.assertEqual(step.label, 'Level 3')
        self.assertEqual(step.message, 'Escalation to decision stakeholders')
        self.assertEqual(step.content, None)
        self.assertEqual(step.file, None)
        self.assertEqual(step.moderators, [])
        self.assertEqual(step.participants, ['bob@acme.com'])
        self.assertTrue(step.machine is not None)

        step = my_steps[3]
        self.assertEqual(step.label, 'Terminated')
        self.assertEqual(step.message, 'Process is closed, yet conversation can continue')
        self.assertEqual(step.content, None)
        self.assertEqual(step.file, None)
        self.assertEqual(step.moderators, [])
        self.assertEqual(step.participants, [])
        self.assertTrue(step.machine is not None)

    def test_step_say(self):

        logging.info("******** step.say")

        with mock.patch.object(my_bot,
                               'say') as mocked:

            step = my_running_steps[0]
            step.say(bot=my_bot)
            mocked.assert_called_with(u'Current state: Level 1 - Initial capture of information')

            step = my_running_steps[1]
            step.say(bot=my_bot)
            mocked.assert_called_with(u'Current state: Level 2 - Escalation to technical experts')

            step = my_running_steps[2]
            step.say(bot=my_bot)
            mocked.assert_called_with(u'Current state: Level 3 - Escalation to decision stakeholders')

            step = my_running_steps[3]
            step.say(bot=my_bot)
            mocked.assert_called_with(u'Current state: Terminated - Process is closed, yet conversation can continue')

    def test_step_trigger(self):

        logging.info("******** step.trigger")

        with mock.patch.object(my_bot,
                               'space') as mocked:

            step = my_running_steps[0]
            step.trigger(bot=my_bot)

            step = my_running_steps[1]
            self.assertFalse(step.machine.started)
            step.trigger(bot=my_bot)
            self.assertTrue(step.machine.started)

            step = my_running_steps[2]
            self.assertFalse(step.machine.started)
            step.trigger(bot=my_bot)
            self.assertTrue(step.machine.started)

            step = my_running_steps[3]
            self.assertFalse(step.machine.started)
            step.trigger(bot=my_bot)
            self.assertTrue(step.machine.started)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
