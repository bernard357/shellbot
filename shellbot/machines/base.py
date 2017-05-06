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

from collections import defaultdict
import logging


class Machine(object):
    """
    Implements a state machine

    The life cycle of a machine can be described as follows::

    1. A machine instance is created and configured::

           >>>bot = ShellBot(...)
           >>>machine = Machine(bot=bot)

           >>>machine.set(states=states, transitions=transitions, ...

    2. The machine is switched on::

           >>>machine.start()
           >>>machine.is_ready
           True

    3. Machine can process events::

           >>>machine.step()

    4. Some machines can be reset, others will raise exceptions::

           >>>machine.reset()

    5. When the machine is coming end of life, resources can be disposed::

           >>>machine.stop()
           >>>machine.is_ready
           False

    credit: Alex Bertsch <abertsch@dropbox.com>   securitybot/state_machine.py
    """

    def __init__(self,
                 bot=None,
                 states=None,
                 transitions=None,
                 initial=None,
                 during=None,
                 on_enter=None,
                 on_exit=None,
                 **kwargs):
        """
        Implements a state machine

        :param bot: the overarching bot
        :type bot: ShellBot

        :param states: All states supported by this machine
        :type states: list of str

        :param transitions: Transitions between states.
            Each transition is a dictionary. Each dictionary must feature
            following keys:
                source (str): The source state of the transition
                target (str): The target state of the transition
            Each dictionary may contain following keys:
                condition (function): A condition that must be true for the
                    transition to occur. If no condition is provided then
                    the state machine will transition on a step.
                action (function): A function to be executed while the
                    transition occurs.
        :type transitions: list of dict

        :param initial: The initial state
        :type initial: str

        :param during: A mapping of states to functions to execute while in
            that state. Each key should map to a callable function.
        :type during: dict

        :param on_enter: A mapping of states to functions to execute when
            entering that state. Each key should map to a callable function.
        :type on_enter: dict

        :param on_exit: A mapping of states to functions to execute when
            exiting that state. Each key should map to a callable function.
        :type on_exit: dict

        Example::

            machine = Machine(bot=bot)

        """
        self.bot = bot

        self.on_init(**kwargs)

        if states is not None:
            self.build(states, transitions, initial, during, on_enter, on_exit)

    def on_init(self, prefix='machine', **kwargs):
        """
        Handles extended initialisation parameters

        :param prefix: the main keyword for configuration of this machine
        :type prefix: str

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_init(self, prefix='my.machine', **kwargs):
                ...

        """
        assert prefix not in (None, '')
        self.prefix = prefix

    def build(self,
            states,
            transitions,
            initial,
            during=None,
            on_enter=None,
            on_exit=None):
        """
        Builds a complete state machine

        :param states: All states supported by this machine
        :type states: list of str

        :param transitions: Transitions between states.
            Each transition is a dictionary. Each dictionary must feature
            following keys:
                source (str): The source state of the transition
                target (str): The target state of the transition
            Each dictionary may contain following keys:
                condition (function): A condition that must be true for the
                    transition to occur. If no condition is provided then
                    the state machine will transition on a step.
                action (function): A function to be executed while the
                    transition occurs.
        :type transitions: list of dict

        :param initial: The initial state
        :type initial: str

        :param during: A mapping of states to functions to execute while in
            that state. Each key should map to a callable function.
        :type during: dict

        :param on_enter: A mapping of states to functions to execute when
            entering that state. Each key should map to a callable function.
        :type on_enter: dict

        :param on_exit: A mapping of states to functions to execute when
            exiting that state. Each key should map to a callable function.
        :type on_exit: dict

        """
        if during is None:
            during = {}
        if on_enter is None:
            on_enter = {}
        if on_exit is None:
            on_exit = {}

        states = sorted(list(set(states)))

        self._states = {}
        for state in states:
            self._states[state] = State(state,
                                        during.get(state, None),
                                        on_enter.get(state, None),
                                        on_exit.get(state, None))

        try:
            self.state = self._states[initial]
        except KeyError:
            raise ValueError(u'Invalid initial state {}'.format(initial))

        self._transitions = defaultdict(list)
        for transition in transitions:
            try:
                source_state = self._states[transition['source']]
            except KeyError:
                if 'source' not in transition:
                    raise ValueError(u'Missing source state')
                else:
                    raise ValueError(u'Invalid source state {}'.format(
                        transition['source']))

            try:
                target_state = self._states[transition['target']]
            except KeyError:
                if 'target' not in transition:
                    raise ValueError(u'Missing target state')
                else:
                    raise ValueError(u'Invalid target state {}'.format(
                        transition['target']))

            item = Transition(source_state,
                              target_state,
                              transition.get('condition', None),
                              transition.get('action', None))

            self._transitions[transition['source']].append(item)

    def step(self, **kwargs):
        """
        Brings some life to the state machine

        This function should report on progress by sending
        messages with one or multiple ``self.bot.say("Whatever message")``.

        """
        self.state.during(**kwargs)

        for transition in self._transitions[self.state.name]:
            if transition.condition(**kwargs):
                logging.debug('Transitioning: {0}'.format(transition))
                transition.action()
                self.state.on_exit()
                self.state = transition.target
                self.state.on_enter()
                break


class State(object):
    """
    Represents a state in the machine

    Each state has a function to perform while it's active, when it's entered
    into, and when it's exited. These functions may be None.
    """
    def __init__(self,
                 name,
                 during=None,
                 on_enter=None,
                 on_exit=None):
        """
        Represents a state in the machine

        :param name: name of the state
        :type name: str

        ;param during: A function to call while this state is active.
        :type during: function

        :param on_enter: A function to call when transitioning into this state.
        :type on_enter: function

        :param on_exit: Function to call when transitioning out of this state.
        :type on_exit: function

        """
        self.name = name
        self._during = during
        self._on_enter = on_enter
        self._on_exit = on_exit

    def __repr__(self):
        """
        Provides a representation of this state

        :rtype: str

        """
        return u"State({0}, {1}, {2}, {3})".format(self.name,
                                                   self._during,
                                                   self._on_enter,
                                                   self._on_exit
                                                   )

    def __str__(self):
        """
        Provides a string handle to this state

        :rtype: str
        """
        return self.name

    def during(self, **kwargs):
        """
        Does some stuff while in this state
        """
        if self._during is not None:
            self._during(**kwargs)

    def on_enter(self):
        """
        Does some stuf while transitioning into this state
        """
        if self._on_enter is not None:
            self._on_enter()

    def on_exit(self):
        """
        Does some stuf while transitioning out of this state
        """
        if self._on_exit is not None:
            self._on_exit()


class Transition(object):
    """
    Represents a transition between two states

    Each transition object holds
    a reference to its source and destination states, as well as the condition
    function it requires for transitioning and the action to perform upon
    transitioning.
    """

    def __init__(self,
                 source,
                 target,
                 condition=None,
                 action=None):
        """
        Represents a transition between two states

        Args:
            source (State): The source State for this transition.
            target (State): The destination State for this transition.
            condition (function): The transitioning condition callback.
            action (function): An action to perform upon transitioning.
        """
        self.source = source
        self.target = target
        self._condition = condition
        self._action = action

    def __repr__(self):
        """
        Provides a representation of this transition

        :rtype: str

        """
        return u"Transition({0}, {1}, {2}, {3})".format(repr(self.source),
                                                        repr(self.target),
                                                        self._condition,
                                                        self._action
                                                        )

    def __str__(self):
        """
        Provides a string handle to this transition

        :rtype: str
        """
        return "{0} => {1}".format(self.source, self.target)

    def condition(self, **kwargs):
        """
        Checks if transition can be triggered

        :return: True or False

        Condition default to True if none is provided
        """
        return True if self._condition is None else self._condition(**kwargs)

    def action(self):
        """
        Does some stuff while transitioning
        """
        if self._action is not None:
            self._action()

