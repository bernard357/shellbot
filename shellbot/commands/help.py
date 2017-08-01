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

from .base import Command


class Help(Command):
    """
    Lists available commands and related usage information
    """

    keyword = u'help'
    information_message = u'Show commands and usage'
    usage_message = u'help <command>'
    usage_template = u"usage: {}"

    def execute(self, bot, arguments=None, **kwargs):
        """
        Lists available commands and related usage information

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        """

        if self.engine.shell.commands == []:
            bot.say(u"No command has been found.")

        elif arguments in (None, ''):
            lines = []

            for key in self.engine.shell.commands:
                command = self.engine.shell.command(key)
                if command.is_hidden:
                    pass

                elif self.allow(bot, command):
                    lines.append(u"{} - {}".format(
                        command.keyword,
                        command.information_message))

            for name in self.engine.list_factory.list_commands():
                item = self.engine.list_factory.get_list(name)
                first = next(iter(item))
                lines.append(u"{} - {}".format(
                    name,
                    u"add participants ({}, ...)".format(first)))

            if lines:
                bot.say(
                    'Available commands:\n'
                    + '\n'.join(lines))

        else:
            command = self.engine.shell.command(arguments)

            if not command:
                bot.say(u"This command is unknown.")

            elif not self.allow(bot, command):
                bot.say(u"This command is unknown.")

            else:
                lines = []
                lines.append(u"{} - {}".format(
                    command.keyword,
                    command.information_message))
                if command.usage_message:
                    lines.append(
                        self.usage_template.format(command.usage_message))
                else:
                    lines.append(
                        self.usage_template.format(command.keyword))

                if lines:
                    bot.say('\n'.join(lines))

    def allow(self, bot, command):
        """
        Allows a command for this bot

        :param bot: Can be a direct channel, or a group channel
        :type bot: ShellBot

        :param command: Can be restricted either to direct or to group channels
        :type command: Command

        :return: True is this command is allowed for this bot, else False
        """
        if command.in_group and not bot.channel.is_direct:
            return True
        if command.in_direct and bot.channel.is_direct:
            return True
        return False
