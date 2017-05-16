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

        for machine in self.machines:
            machine.tick()

        logging.info(u"End of the sequence")
