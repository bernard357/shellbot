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


class Sequence(object):
    """
    Implements a sequence of multiple machines

    This implements one state machine that is actually a combination
    of multiple sub-machines, ran in sequence. When one sub-machine stops,
    the next one is activated.

    Example::

        input_1 = Input( ... )
        input_2 = Input( ... )
        sequence = Sequence([input_1, input_2])
        sequence.start()

    In this example, the first machine is started, then when it ends
    the second machine is triggered.

    """
    def __init__(self, bot=None, machines=None, **kwargs):
        """
        Implements a sequence of multiple machines

        :param machines: the sequence of machines to be ran
        :type machines: list of Machine

        """
        self.bot = bot
        self.machines = machines

        self.lock = Lock()

        # prevent Manager() process to be interrupted
        handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.mutables = Manager().dict()

        # restore current handler for the rest of the program
        signal.signal(signal.SIGINT, handler)

        self.on_init(**kwargs)

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

        logging.warning(u"Resetting sequence")

        # reset all sub machines
        for machine in self.machines:
            machine.reset()

        # do the rest
        self.on_reset()

        return True

    def on_reset(self):
        """
        Adds processing to machine reset

        This function should be expanded in sub-class, where necessary.

        """
        pass

    def start(self):
        """
        Starts the sequence

        :return: either the process that has been started, or None

        This function starts a separate thread to run machines
        in the background.
        """
        process = Process(target=self.run)  # do not daemonize
        process.start()
        return process

    def stop(self):
        """
        Stops the sequence

        This function stops the underlying machine and breaks the sequence.
        """
        if self.is_running:
            self.set('is_running', False)

        index = self.get('_index')
        if index:
            machine = self.machines[index]
            machine.stop()
            self.set('_index', None)

    def run(self):
        """
        Continuously ticks the sequence

        This function is looping in the background, and calls the function
        ``step()`` at regular intervals.

        The loop is stopped when the parameter ``general.switch``
        is changed in the context. For example::

            bot.context.set('general.switch', 'off')

        """
        logging.info(u"Beginning of the sequence")
        self.set('is_running', True)

        index = 0
        while index < len(self.machines):

            logging.info(u"- running machine #{}".format(index+1))
            self.set('_index', index)
            machine = self.machines[index]

            process = machine.start()
            if process:
                process.join()
            index += 1

            if not self.is_running:
                break

        self.set('_index', None)

        logging.info(u"End of the sequence")
        self.set('is_running', False)

    @property
    def is_running(self):
        """
        Determines if this machine is runnning

        :return: True or False
        """
        return self.get('is_running', False)
