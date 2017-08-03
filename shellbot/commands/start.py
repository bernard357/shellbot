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

class Start(Command):
    """
    Restarts the underlying state machine

    This command restarts the current state machine. A typical use case is when
    a person interacts with the bot over a direct channel for the initial
    gathering of data. For this kind of situation, the person will type
    ``start`` each time she initiates a new sequence.

    You can check ``examples/direct.py`` as a practical tutorial.

    Note: this command has no effect on a running machine.

    Example to load the command in the engine::

        engine = Engine(commands=['shellbot.commands.start', ...])

    By default the command is visible only from direct channels. You can change
    this by configuring an instance before it is given to the engine::

        start = Start()
        start.in_group = True

        engine = Engine(commands=[start, ...])

    Obviously, this command should not be loaded if your use case does not rely
    on state machines, or if your state machines never end.

    """

    keyword = 'start'
    information_message = u"Start a new sequence"

    in_direct = True
    in_group = False

    def execute(self, bot, arguments=None, **kwargs):
        """
        Restarts the underlying state machine

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        This function calls the ``restart()`` function of the underlying
        state machine. It also transmits text
        typed by the end user after the command verb, and any other
        parameters received from the shell, e.g., attachment, etc.

        Note: this command has no effect on a running machine.
        """
        if not bot.machine:
            bot.say(u"No state machine is available")

        elif not bot.machine.restart(arguments=arguments, **kwargs):
            bot.say(u"Cannot restart the state machine")
