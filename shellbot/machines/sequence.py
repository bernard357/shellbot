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

    Machines are provided and activated one by one in sequence.

    Example::

        input_1 = Input( ... )
        input_2 = Input( ... )
        sequence = Sequence([input_1, input_2])
        sequence.start()

    In this example, the first machine is started, then when it ends
    the second machine is triggered.

    """
    def __init__(self, machines=None):
        """
        Implements a sequence of multiple machines

        :param machines: the sequence of machines to be ran
        :type machines: list of Machine

        """
        self.machines = machines

        self.lock = Lock()

        # prevent Manager() process to be interrupted
        handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.mutables = Manager().dict()

        # restore current handler for the rest of the program
        signal.signal(signal.SIGINT, handler)

    def get(self, key, default=None):
        """
        Retrieves the value of one key
        """

        with self.lock:

            value = self.mutables.get(key, default)

            if value is not None:
                return value

            return default

    def set(self, key, value):
        """
        Remembers the value of one key
        """

        with self.lock:

            self.mutables[key] = value

    def reset(self):
        """
        Resets a state machine before it is restarted

        This function move back to the initial state, if the machine is not
        running.

        Example::

            if new_cycle():
                machine.reset()
                machine.start()

        """
        if self.is_running:
            logging.warning(u"Cannot reset a running sequence")
        else:
            logging.warning(u"Resetting sequence")

            for machine in self.machines:
                machine.reset()

            self.on_reset()

    def on_reset(self):
        pass

    def start(self):
        """
        Runs the sequence

        :param tick: The duration set for each tick
        :type tick: float

        :return: either the process that has been started, or None

        This function starts a separate thread to tick the machine
        in the background.
        """
        p = Process(target=self.tick)
        p.start()
        return p

    def tick(self):
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

        for machine in self.machines:
            machine.tick()

        logging.info(u"End of the sequence")
        self.set('is_running', False)

    @property
    def is_running(self):
        """
        Determines if this machine is runnning

        :return: True or False
        """
        return self.get('is_running', False)


