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

class State(Command):
    """
    Displays process status

    >>>state = State(steps=steps)
    >>>shell.load_command(state)

    """

    keyword = u'state'
    information_message = u'Display current state in process'

    def execute(self, arguments=None):
        """
        Displays process status
        """
        if self.bot.steps is None:
            raise AttributeError(u'State machine has not been initialised')

        step = self.bot.steps.step
        if step is None:
            self.bot.say(u"Current state is undefined")
        else:
            self.bot.say(u"Current state: {} - {}".format(step.label,
                                                          step.message))
