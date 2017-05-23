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

from shellbot import Command

class Next(Command):
    """
    Moves process to next state

    >>>next = Next(steps=steps)
    >>>shell.load_command(next)

    """

    keyword = u'next'
    information_message = u'Move process to next state'

    def execute(self, arguments=None):
        """
        Moves process to next state
        """
        if self.bot.steps is None:
            raise AttributeError(u'State machine has not been initialised')

        current = self.bot.steps.step
        new = self.bot.steps.next()
        if new is None:
            self.bot.say(u"Current state is undefined")
            return

        if (current is not None) and (current.label == new.label):
            self.bot.say(u"Current state: {} - {}".format(current.label,
                                                          current.message))
            return

        self.bot.say(u"New state: {} - {}".format(new.label,
                                                  new.message),
                     content=new.markdown)

        self.bot.add_moderators(new.moderators)
        self.bot.add_participants(new.participants)
