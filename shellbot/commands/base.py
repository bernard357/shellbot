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


class Command(object):
    """
    Implements one command
    """

    def __init__(self, bot=None, **kwargs):
        self.bot = bot
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.on_init()

    def on_init(self):
        """
        Handles extended initialisation

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_init(self):
                self.bot.register('bond', self.on_bond)
                self.bot.register('dispose', self.on_dispose)

        """
        pass

    def execute(self, arguments=None):
        """
        Executes this command

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        This function should report on progress by sending
        messages with one or multiple ``self.shell.say("Whatever response")``.

        """
        if self.information_message:
            self.bot.say(self.information_message)

    keyword = None      # verb or token for this command

    information_message = None    # basic information for this command

    usage_message = None    # usage information for this command

    is_interactive = True    # this command should be processed interactively

    is_hidden = False    # this command should be listed by 'help'
