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
from Queue import Empty


class Worker(object):
    """
    Executes non-interactive commands
    """

    def __init__(self, bot=None):
        self.bot = bot
        self.context = bot.context
        self.inbox = bot.inbox
        self.shell = bot.shell

    def work(self):
        """
        Continuously processes commands

        :param context: the context shared across processes
        :type context: context

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            worker = Worker(bot=my_bot)

            process = Process(target=worker.work)
            process.daemon = True
            process.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            context.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            inbox.put(Exception('EOQ'))

        """
        logging.info(u"Starting worker")

        self.context.set('worker.counter', 0)
        self.context.set('worker.busy', False)

        try:
            while self.context.get('general.switch', 'on') == 'on':
                try:
                    item = self.inbox.get(True, 0.1)
                    if isinstance(item, Exception):
                        break
                    counter = self.context.increment('worker.counter')
                    self.context.set('worker.busy', True)
                    self.process(item, counter)

                    self.context.set('worker.busy', False)
                except Empty:
                    pass

        except KeyboardInterrupt:
            pass

        finally:
            logging.info(u"Worker has been stopped")

    def process(self, item, counter):
        """
        Processes one action

        Example actions:

            ('help', 'some_command')
            ('version', '')

        """
        logging.debug(u'Worker is working on {}'.format(counter))

        (verb, arguments) = item

        try:
            if verb in self.shell.commands:
                command = self.shell.command(verb)
                command.execute(arguments)

            elif '*default' in self.shell.commands:
                command = self.shell.command('*default')
                command.execute(arguments)

            else:
                self.bot.say(
                    u"Sorry, I do not know how to handle '{}'".format(verb))

        except Exception:
            self.bot.say(
                u"Sorry, I do not know how to handle '{}'".format(verb))
            raise
