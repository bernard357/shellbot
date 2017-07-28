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
from multiprocessing import Process
from six import string_types
import time


class Observer(Process):
    """
    Dispatches inbound records to downwards updaters
    """

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, engine=None):
        """
        Dispatches inbound records to downwards updaters

        :param engine: the overarching engine
        :type engine: Engine

        """
        Process.__init__(self)
        self.engine = engine

    def run(self):
        """
        Continuously handle inbound records and commands

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            observer = Observer(engine=my_engine)
            observer.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            engine.fan.put(None)

        """
        logging.info(u"Starting observer")

        try:
            self.engine.set('observer.counter', 0)
            while self.engine.get('general.switch', 'on') == 'on':

                if self.engine.fan.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.engine.fan.get(True, 0.1)
                    if item is None:
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        logging.info(u"Observer has been stopped")

    def process(self, item):
        """
        Handles one record or command

        :param item: the record or command
        :type item: str or object

        """

        counter = self.engine.context.increment('observer.counter')
        logging.debug(u'Observer is working on {}'.format(counter))

        logging.debug(u"Observer is not finished yet -- Work in progress")
