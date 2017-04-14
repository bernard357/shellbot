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

from shellbot.commands.base import Command

class State(Command):
    """
    Displays process status
    """

    keyword = 'state'
    information_message = 'Displays process current state.'

    def execute(self, verb, arguments=None):
        """
        Displays software version
        """
        state = self.context.get('process.current')
        if state is None:
            state = self.context.get('process.initial')
        if state is None:
            state = '*unknown*'
        self.shell.say("Current state: {}".format(state))
