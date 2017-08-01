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

import time

from .base import Command


class Default(Command):
    """
    Handles unmatched command

    This function looks for a named list and adds participants accordingly.
    Note that only list with attribute ``as_command`` set to true are
    considered.

    In other cases, the end user is advised that the command is unknown.
    """

    keyword = u'*default'
    information_message = u'Handle unmatched command'
    is_hidden = True

    participants_message = u"Adding participants from '{}'"
    default_message = u"Sorry, I do not know how to handle '{}'"

    def execute(self, bot, arguments=None, **kwargs):
        """
        Handles unmatched command

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        Arguments provided should include all of the user input, including
        the first token that has not been recognised as a valid command.
        """
        list = bot.engine.list_factory.get_list(arguments)
        if list and list.as_command:
            bot.say(self.participants_message.format(arguments))
            persons = [x for x in list]
            bot.add_participants(persons)

        else:
            bot.say(self.default_message.format(arguments))
