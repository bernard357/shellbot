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

    Example::

        steps = [

            Step({
                'label': u'Level 1',
                'message': u'Initial capture of information',
            }, 1),

            Step({
                'label': u'Level 2',
                'message': u'Escalation to technical experts',
                'moderators': 'alice@acme.com',
            }, 2),

            Step({
                'label': u'Level 3',
                'message': u'Escalation to decision stakeholders',
                'participants': 'bob@acme.com',
            }, 3),

            Step({
                'label': u'Terminated',
                'message': u'Process is closed, yet conversation can continue',
            }, 4),

        ]
        machine = Steps(bot=bot, steps=steps)
        machine.start()
        ...


    """

    def on_init(self,
                steps=None,
                prefix='steps',
                **kwargs):
        """
        Handles extended initialisation parameters

        :param steps: The steps for this process
        :type steps: list of Step or of dict

        :param prefix: the main keyword for configuration of this machine
        :type prefix: str

        """
        super(Steps, self).on_init(prefix, **kwargs)

        self.steps = []
        if steps:
            for item in steps:
                if isinstance(item, dict):
                    self.steps.append(Step(item, len(self.steps)+1))
                else:
                    self.steps.append(item)

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
        """
        if not self.steps or len(self.steps) < 1:
            return None  # no steps have been set

        index = self.get('_index')

        if index is None:
            index = 0
        elif index < len(self.steps)-1:
            index += 1
        else:
            return None  # all steps have been used

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

        return not machine.is_running()

    def if_ready(self, **kwargs):
        """
        Checks if state machine can engage on first step

        To be implemented in sub-class where complex initialization activities
        are required.
        """
        return True

    def if_next(self, **kwargs):
        """
        Checks if next step should be engaged

        :param event: a label of event submitted to the machine
        :type event: str

        This function is used by the state machine for testing the transition
        to the next available step in the process.

        Since this function is an integral part of the state machine itself, it
        should be triggered via a call of the ``step()`` member function.

        For example::

            machine.step(event='next')

        """

        if kwargs.get('event') == 'next':
            return True

        return False

    def if_end(self, **kwargs):
        """
        Checks if all steps have been used

        Since this function is an integral part of the state machine itself, it
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

        self.moderators = attributes.get('moderators', [])
        if isinstance(self.moderators, string_types):
            self.moderators = [self.moderators]

        self.participants = attributes.get('participants', [])
        if isinstance(self.participants, string_types):
            self.participants = [self.participants]

        self.machine = attributes.get('machine', None)

    def say(self, bot):
        """
        Reports on this step

        :param bot: the bit to use
        :type bot: ShellBot

        This function posts to the chat space some information on this step.

        Example::

            step.say(bot)

        """
        bot.say(u"Current state: {} - {}".format(self.label,
                                                 self.message))

    def trigger(self, bot):
        """
        Triggers a step

        :param bot: the bit to use
        :type bot: ShellBot

        This function does everything that is coming with a step:
        - send a message to the chat space,
        - maybe in MarkDown or HTML,
        - maybe with some attachment,
        - add participants and/or moderators to the space,
        - start a state machine


        Example::

            step.trigger(bot)

        """
        bot.say(u"New state: {} - {}".format(self.label,
                                             self.message),
                content=self.content,
                file=self.file)

        bot.add_moderators(self.moderators)
        bot.add_participants(self.participants)

        if self.machine:
            self._step_process = self.machine.start()
