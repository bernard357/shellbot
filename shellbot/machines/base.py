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
from multiprocessing import Manager, Lock, Process, Queue
import signal
import time


class Machine(object):
    """
    Implements a state machine

    The life cycle of a machine can be described as follows::

    1. A machine instance is created and configured::

           a_bot = ShellBot(...)
           machine = Machine(bot=a_bot)

           machine.set(states=states, transitions=transitions, ...

    2. The machine is switched on and ticked at regular intervals::

           machine.start()

    3. Machine can process more events than ticks::

           machine.execute('hello world')

    4. When a machine is expecting data from the chat space, it listens
       from the ``fan`` queue used by the shell::

           engine.fan.put('special command')

    5. When the machine is coming end of life, resources can be disposed::

           machine.stop()

    credit: Alex Bertsch <abertsch@dropbox.com>   securitybot/state_machine.py
    """

    DEFER_DURATION = 0.0  # time to pause before working, in seconds
    TICK_DURATION = 0.2  # time to wait between ticks, in seconds

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

        :param bot: the bot linked to this machine
        :type : ShellBot

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

        self.lock = Lock()

        # prevent Manager() process to be interrupted
        handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.mutables = Manager().dict()

        # restore current handler for the rest of the program
        signal.signal(signal.SIGINT, handler)

        self.mixer = Queue()

        self.on_init(**kwargs)

        if states:
            self.build(states, transitions, initial, during, on_enter, on_exit)

    def on_init(self, **kwargs):
        """
        Adds to machine initialisation

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_init(self, prefix='my.machine', **kwargs):
                ...

        """
        pass

    def get(self, key, default=None):
        """
        Retrieves the value of one key

        :param key: one attribute of this state machine instance
        :type key: str

        :param default: default value is the attribute has not been set yet
        :type default: an type that can be serialized

        This function can be used across multiple processes, so that
        a consistent view of the state machine is provided.
        """

        with self.lock:

            value = self.mutables.get(key, default)

            if value is not None:
                return value

            return default

    def set(self, key, value):
        """
        Remembers the value of one key

        :param key: one attribute of this state machine instance
        :type key: str

        :param value: new value of the attribute
        :type value: an type that can be serialized

        This function can be used across multiple processes, so that
        a consistent view of the state machine is provided.
        """

        with self.lock:
            self.mutables[key] = value

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

        self._states = dict()
        for state in states:
            self._states[state] = State(state,
                                        during.get(state, None),
                                        on_enter.get(state, None),
                                        on_exit.get(state, None))

        try:
            self.mutables['initial_state'] = self._states[initial].name
            self.mutables['state'] = self.mutables['initial_state']
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

    def state(self, name):
        """
        Provides a state by name

        :param name: The label of the target state
        :type name: str

        :return: State

        This function raises KeyError if an unknown name is provided.
        """
        return self._states[name]

    @property
    def current_state(self):
        """
        Provides current state

        :return: State

        This function raises AttributeError if it is called before ``build()``.
        """
        try:
            name = self.mutables['state']
        except KeyError:
            raise AttributeError('Machine has not been built')

        return self._states[name]

    def reset(self):
        """
        Resets a state machine before it is restarted

        :return: True if the machine has been actually reset, else False

        This function moves a state machine back to its initial state.
        A typical use case is when you have to recycle a state machine
        multiple times, like in the following example::

            if new_cycle():
                machine.reset()
                machine.start()

        If the machine is running, calling ``reset()`` will have no effect
        and you will get False in return. Therefore, if you have to force
        a reset, you may have to stop the machine first.

        Example of forced reset::

            machine.stop()
            machine.reset()

        """
        if self.is_running:
            logging.warning(u"Cannot reset a running state machine")
            return False

        # purge the mixer queue
        while not self.mixer.empty():
            self.mixer.get()

        # restore initial state
        self.set('state', self.get('initial_state'))
        logging.warning(u"Resetting machine to '{}'".format(
            self.current_state.name))

        # do the rest
        self.on_reset()

        return True

    def on_reset(self):
        """
        Adds processing to machine reset

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_reset(self):
                self.sub_machine.reset()

        """
        pass

    def step(self, **kwargs):
        """
        Brings some life to the state machine

        Thanks to ``**kwargs``, it is easy to transmit parameters
        to underlying functions:
        - ``current_state.during(**kwargs)``
        - ``transition.condition(**kwargs)``

        Since parameters can vary on complex state machines, you are advised
        to pay specific attention to the signatures of related functions.
        If you expect some parameter in a function, use ``kwargs.get()``to
        get its value safely.

        For example, to inject the value of a gauge in the state machine
        on each tick::

            def remember(**kwargs):
                gauge = kwargs.get('gauge')
                if gauge:
                    db.save(gauge)

            during = { 'measuring', remember }

            ...

            machine.build(during=during, ... )

            while machine.is_running:
                machine.step(gauge=get_measurement())

        Or, if you have to transition on a specific threshold for a gauge,
        you could do::

            def if_threshold(**kwargs):
                gauge = kwargs.get('gauge')
                if gauge > 20:
                    return True
                return False

            def raise_alarm():
                mail.post_message()

            transitions = [

                {'source': 'normal',
                 'target': 'alarm',
                 'condition': if_threshold,
                 'action': raise_alarm},

                 ...

                ]

            ...

            machine.build(transitions=transitions, ... )

            while machine.is_running:
                machine.step(gauge=get_measurement())

        Shellbot is using this mechanism for itself, and the function can be
        called at various occasions:
        - machine tick - This is done at regular intervals in time
        - input from the chat - Typically, in response to a question
        - inbound message - Received from subscription, over the network

        Following parameters are used for machine ticks:
        - event='tick' - fixed value

        Following parameters are used for chat input:
        - event='input' - fixed value
        - arguments - the text that is submitted from the chat

        Following parameters are used for subscriptions:
        - event='inbound' - fixed value
        - message - the object that has been transmitted

        This machine should report on progress by sending
        messages with one or multiple ``self.bot.say("Whatever message")``.

        """
        self.current_state.during(**kwargs)

        for transition in self._transitions[self.current_state.name]:
            if transition.condition(**kwargs):
                logging.debug('Transitioning: {0}'.format(transition))
                transition.action()
                self.current_state.on_exit()
                self.mutables['state'] = transition.target.name
                self.current_state.on_enter()
                break

    def start(self, tick=None, defer=None):
        """
        Starts the machine

        :param tick: The duration set for each tick (optional)
        :type tick: positive number

        :param defer: wait some seconds before the actual work (optional)
        :type defer: positive number

        :return: either the process that has been started, or None

        This function starts a separate thread to tick the machine
        in the background.
        """
        if tick:
            assert tick > 0.0  # number of seconds
            self.TICK_DURATION = tick

        if defer is not None:
            assert defer >= 0.0  # number of seconds
            self.DEFER_DURATION = defer

        process = Process(target=self.run)  # do not daemonize
        process.start()

        while not self.is_running:  # prevent race condition on stop()
            time.sleep(0.001)

        return process

    def restart(self, **kwargs):
        """
        Restarts the machine

        This function is very similar to reset(), except that it also
        starts the machine on successful reset. Parameters given to
        it are those that are expected by start().

        Note: this function has no effect on a running machine.
        """
        if not self.reset():
            return False

        self.start(**kwargs)
        return True

    def stop(self):
        """
        Stops the machine

        This function sends a poison pill to the queue that is read
        on each tick.
        """
        if self.is_running:
            self.mixer.put(None)
            time.sleep(self.TICK_DURATION+0.05)

    def run(self):
        """
        Continuously ticks the machine

        This function is looping in the background, and calls
        ``step(event='tick')`` at regular intervals.

        The recommended way for stopping the process is to call the function
        ``stop()``. For example::

            machine.stop()

        The loop is also stopped when the parameter ``general.switch``
        is changed in the context. For example::

            engine.set('general.switch', 'off')

        """
        logging.info(u"Starting machine")
        self.set('is_running', True)
        self.on_start()

        time.sleep(self.DEFER_DURATION)

        try:
            while self.bot.engine.get('general.switch', 'on') == 'on':

                try:
                    if self.mixer.empty():
                        self.on_tick()
                        time.sleep(self.TICK_DURATION)
                        continue

                    item = self.mixer.get(True, self.TICK_DURATION)
                    if item is None:
                        logging.debug('Stopping machine on poison pill')
                        break

                    logging.debug('Processing item')
                    self.execute(arguments=item)

                except Exception as feedback:
                    logging.exception(feedback)
                    break

        except KeyboardInterrupt:
            pass

        self.on_stop()
        self.set('is_running', False)
        logging.info(u"Machine has been stopped")

    def on_start(self):
        """
        Adds to machine start

        This function is invoked when the machine is started or restarted.
        It can be expanded in sub-classes where required.

        Example::

            def on_start(self):  # clear bot store on machine start
                self.bot.forget()
        """
        pass

    def on_stop(self):
        """
        Adds to machine stop

        This function is invoked when the machine is stopped.
        It can be expanded in sub-classes where required.

        Example::

            def on_stop(self):  # dump bot store on machine stop
                self.bot.publisher.put(
                    self.bot.id,
                    self.bot.recall('input'))
        """
        pass

    def on_tick(self):
        """
        Processes one tick
        """
        self.step(event='tick')

        message = self.bot.subscriber.get()
        if message:
            self.step(event='inbound', message=message)

    def execute(self, arguments=None, **kwargs):
        """
        Processes data received from the chat

        :param arguments: input to be injected into the state machine
        :type arguments: str is recommended

        This function can be used to feed the machine asynchronously
        """
        self.step(event='input', arguments=arguments, **kwargs)

    @property
    def is_running(self):
        """
        Determines if this machine is runnning

        :return: True or False
        """
        return self.get('is_running', False)


class State(object):
    """
    Represents a state of the machine

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
        Does some stuff while transitioning out of this state
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
