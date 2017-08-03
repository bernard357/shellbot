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

    This command sends an event to the current state machine. This can be
    handled by the state machine, e.g., a ``Steps`` instance, for moving forward.

    You can check ``examples/pushy.py`` as a practical tutorial.

    Example to load the command in the engine::

        engine = Engine(commands=['shellbot.commands.step', ...])

    By default, the command sends the event ``next`` to the state machine.
    This can be changed while creating your own command instance, before
    it is given to the engine. For example::

        step = Steps(event='super_event')
        engine = Engine(commands=[step, ...])

    Obviously, this command should not be loaded if your use case does not rely
    on state machines, or if your state machines do not expect events
    from human beings.

    """

    keyword = u'step'
    information_message = u'Move process to next step'

    event = 'next'  # understood by machines/steps

    def execute(self, bot, arguments=None, **kwargs):
        """
        Moves underlying state machine to the next step

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        This function calls the ``step()`` function of the underlying
        state machine and provides a static event. It also transmits text
        typed by the end user after the command verb, and any other
        parameters received from the shell, e.g., attachment, etc.
        """
        if bot.machine:
            bot.machine.step(event=self.event,
                             arguments=arguments,
                             **kwargs)
        else:
            bot.say(u"No state machine is available")
