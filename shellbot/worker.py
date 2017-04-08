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
import random
import time

class Worker(object):
    """
    Takes activities from the inbox and puts reports in the outbox
    """

    def __init__(self, inbox, shell):
        self.inbox = inbox
        self.shell = shell

    def work(self, context):
        print("Starting worker")

        self.context = context
        self.context.set('worker.counter', 0)
        self.context.set('worker.busy', False)

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


    def process(self, item, counter):
        """
        Processes one action

        Example actions:

            ('help', 'some_command')
            ('version', '')

        """
        print('Worker is working on {}'.format(counter))

        (verb, arguments) = item

        try:
            if verb in self.shell.commands.keys():
                command = self.shell.commands[verb]
                command.execute(verb, arguments)

            elif '*' in self.shell.commands.keys():
                command = self.shell.commands['*']
                command.execute(verb, arguments)

            else:
                self.shell.say(
                    "Sorry, I do not know how to handle '{}'".format(verb))

        except Exception as feedback:
            self.shell.say(
                "Sorry, I do not know how to handle '{}'".format(verb))
            raise
