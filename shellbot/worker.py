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
import time


class Worker(object):
    """
    Executes non-interactive commands
    """

    def __init__(self, engine=None):
        """
        Executes non-interactive commands

        :param engine: the overarching engine
        :type engine: Engine

        """
        self.engine = engine

    def start(self):
        """
        Starts the working process

        :return: either the process that has been started, or None

        This function starts a separate daemonic process to work
        in the background.
        """
        p = Process(target=self.run)
        p.daemon = True
        p.start()
        return p

    def run(self):
        """
        Continuously processes commands

        :param context: the context shared across processes
        :type context: context

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in the background, like
        in the following example::

            worker = Worker(engine=my_engine)
            handle = worker.start()

            ...

            handle.join()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            context.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            inbox.put(Exception('EOQ'))

        """
        logging.info(u"Starting worker")

        self.engine.set('worker.counter', 0)
        self.engine.set('worker.busy', False)

        try:
            while self.engine.get('general.switch', 'on') == 'on':

                if self.engine.inbox.empty():
                    time.sleep(0.005)
                    continue

                try:
                    item = self.engine.inbox.get(True, 0.1)
                    if item is None:
                        break

                    self.engine.set('worker.busy', True)
                    self.process(item)
                    self.engine.set('worker.busy', False)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        finally:
            logging.info(u"Worker has been stopped")

    def process(self, item):
        """
        Processes one action

        :param item: the action to perform
        :type item: list or tuple

        Example actions::

            worker.process(item=('help', 'some_command', space_id))

            worker.process(item=('version', '', space_id))

        """
        (verb, arguments, space_id) = item

        counter = self.engine.context.increment('worker.counter')
        logging.debug(u'Worker is working on {} ({})'.format(verb, counter))

        bot = self.engine.get_bot(space_id)

        try:
            if verb in self.engine.shell.commands:
                command = self.engine.shell.command(verb)
                command.execute(bot, arguments)

            elif '*default' in self.engine.shell.commands:
                command = self.engine.shell.command('*default')
                command.execute(bot, ' '.join([verb, arguments]).rstrip())

            else:
                bot.say(
                    u"Sorry, I do not know how to handle '{}'".format(verb))

        except Exception:
            bot.say(
                u"Sorry, I do not know how to handle '{}'".format(verb))
            raise
