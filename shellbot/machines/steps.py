# -*- coding: utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from six import string_types

from .base import Machine


class Steps(Machine):
    """
    Implements a linear process with multiple steps

    This implements a state machine that appears as a phased process to chat
    participants. On each, it can add new participants, display
    some information, and run a child state machine..

    For example, to run an escalation process::

        po_input = Input( ... )
        details_input = Input( ... )

        decision_menu = Menu( ...)

        steps = [

            {
                'label': u'Level 1',
                'message': u'Initial capture of information',
                'machine': Sequence([po_input, details_input]),
            },

            {
                'label': u'Level 2',
                'message': u'Escalation to technical experts',
            },

            {
                'label': u'Level 3',
                'message': u'Escalation to decision stakeholders',
                'participants': 'bob@acme.com',
                'machine': decision_menu,
            },

            {
                'label': u'Terminated',
                'message': u'Process is closed, yet conversation can continue',
            },

        ]
        machine = Steps(bot=bot, steps=steps)
        machine.start()
        ...


    """

    def on_init(self,
                steps=None,
                **kwargs):
        """
        Handles extended initialisation parameters

        :param steps: The steps for this process
        :type steps: list of Step or list of dict

        """
        super(Steps, self).on_init(**kwargs)

        self.steps = []
        if steps:
            for item in steps:
                if isinstance(item, dict):
                    self.steps.append(Step(item, len(self.steps)+1))
                else:
                    self.steps.append(item)

            logging.debug(u"Adding steps:")
            for step in self.steps:
                logging.debug(u"- {}".format(step.label))

        states = ['begin',
                  'running',
                  'completed',
                  'end']

        transitions = [

            {  # engage on first step as soon as we are ready
             'source': 'begin',
             'target': 'running',
             'condition': self.if_ready,
             'action': self.next_step,
            },

            {  # wait for the underlying machine of this step to complete
             'source': 'running',
             'target': 'completed',
             'condition': self.step_has_completed,
            },

            {  # start next step if there is one and if we are ready for it
             'source': 'completed',
             'target': 'running',
             'condition': self.if_next,
             'action': self.next_step,
            },

            {  # end this state machine
             'source': 'completed',
             'target': 'end',
             'condition': self.if_end,
             'action': self.stop,
            },

        ]

        self.build(states=states,
                   transitions=transitions,
                   initial='begin')

    def on_reset(self):
        """
        Restore initial state of this machine

        If a sub-machine is running at current step, it is stopped first.
        """

        current = self.current_step
        if current:
            current.stop()

        logging.debug(u"- seeking back before first step")
        self.set('_index', None)

    @property
    def current_step(self):
        """
        Gets current step

        :return: current step, or None
        """
        index = self.get('_index')
        if index is None:
            return None

        return self.steps[index]

    def next_step(self):
        """
        Moves to next step

        :return: current step, or None

        This function loads and runs the next step in the process, if any.
        If all steps have been consumed it returns None.

        If a sub-machine is running at current step, it is stopped before
        moving to the next step.

        """
        logging.debug(u"Moving to next step")

        if not self.steps or len(self.steps) < 1:
            logging.debug(u"- no steps have ben set")
            return None

        index = self.get('_index')

        if index is None:
            index = 0
        elif index < len(self.steps)-1:
            index += 1
        else:
            logging.debug(u"- all steps have ben consumed")
            return None

        current = self.current_step
        if current:
            current.stop()

        logging.debug(u"- triggering step #{}".format(index+1))
        self.set('_index', index)
        step = self.steps[index]
        step.trigger(bot=self.bot)
        return step

    def step_has_completed(self, **kwargs):
        """
        Checks if the machine for this step has finished its job

        :return: False if the machine is still running, True otherwise
        """
        step = self.current_step
        if step is None:
            return True

        machine = step.machine
        if machine is None:
            return True

        return not machine.is_running

    def if_ready(self, **kwargs):
        """
        Checks if state machine can engage on first step

        To be overlaid in sub-class where complex initialization activities
        are required.

        Example::

            class MyMachine(Machine):

                def if_ready(self, **kwargs):
                    if kwargs.get('phase') == 'warming up':
                        return False
                    else:
                        return True

        """
        return True

    def if_next(self, **kwargs):
        """
        Checks if next step should be engaged

        :param event: a label of event submitted to the machine
        :type event: str

        This function is used by the state machine for testing the transition
        to the next available step in the process.

        Since this function is an integral part of the state machine, it
        should be triggered via a call of the ``step()`` member function.

        For example::

            machine.step(event='next')

        """

        if kwargs.get('event') == 'next':
            logging.debug(u"- asked to move to next step")
            return True

        return False

    def if_end(self, **kwargs):
        """
        Checks if all steps have been used

        Since this function is an integral part of the state machine, it
        should be triggered via a call of the ``step()`` member function.

        For example::

            machine.step(event='tick')

        """

        index = self.get('_index')

        if index and index >= len(self.steps)-1:
            return True  # all steps have been used

        return False


class Step(object):
    """
    Represents a step in a linear process
    """

    def __init__(self, attributes, index):
        """
        Represents a step in a linear process

        :param attributes: the dict to use
        :type attributes: dict

        :param index: index of this step
        :type index: int

        """
        self.label = attributes.get('label', u'Step {}'.format(index))

        self.message = attributes.get('message',
                                      u'(no description is available)')

        self.content = attributes.get('content', None)

        self.file = attributes.get('file', None)

        self.participants = attributes.get('participants', [])
        if isinstance(self.participants, string_types):
            self.participants = [self.participants]

        self.machine = attributes.get('machine', None)

    def __str__(self):
        """
        Returns a human-readable string representation of this object.
        """
        return u"{} - {}".format(self.label, self.message)

    def say(self, bot):
        """
        Reports on this step

        :param bot: the bit to use
        :type bot: ShellBot

        This function posts to the chat space some information on this step.

        Example::

            step.say(bot)

        """
        bot.say(
            u"Current state: {} - {}".format(self.label, self.message))

    def trigger(self, bot):
        """
        Triggers a step

        :param bot: the bot to use
        :type bot: ShellBot

        This function does everything that is coming with a step:
        - send a message to the chat space,
        - maybe in MarkDown or HTML,
        - maybe with some attachment,
        - add participants to the channel,
        - reset and start a state machine

        Example::

            step.trigger(bot)

        """
        bot.say(
            u"New state: {} - {}".format(self.label, self.message))

        if self.content or self.file:
            bot.say(' ',
                    content=self.content,
                    file=self.file)

        bot.add_participants(self.participants)

        if self.machine:
            self.machine.stop()
            self.machine.reset()
            self._step_process = self.machine.start()

    def stop(self):
        """
        Stops a step
        """
        if self.machine:
            self.machine.stop()
