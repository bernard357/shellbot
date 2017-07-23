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

from .base import Command

class Step(Command):
    """
    Moves underlying state machine to the next step

    Example::

        step = Step()
        shell.load_command(step)

    This command only applies when the bot has a state machine.
    You can check ``examples/escalation.py`` to get a concrete use case.

    """

    keyword = u'step'
    information_message = u'Move process to next step'

    def execute(self, bot, arguments=None):
        """
        Moves underlying state machine to the next step

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        This function raises AttributeError when the bot has
        not been initialised with a suitable Machine.
        """
        if bot.machine:
            bot.machine.step(event='next')
        else:
            bot.say(u"No state machine is available")
