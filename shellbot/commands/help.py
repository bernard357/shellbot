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

from base import Command

help_markdown = """
Some commands that may prove useful:
- show status: @plumby status
- list categories: @plumby list
- list templates: @plumby list analytics
- use template: @plumby use analytics/hadoop-cluster
- deploy template: @plumby deploy
- get information: @plumby information
- stop servers: @plumby stop
- start servers: @plumby start
- destroy resources: @plumby dispose
"""

class Help(Command):
    """
    Lists available commands and related usage information
    """

    def do_help(self, arguments=None):
        self.shell.say({'markdown': help_markdown})

    keyword = u'help'
    information_message = u'Show commands and usage.'
    usage_message = u'help <command>'

    def execute(self, arguments=None):
        """
        Lists available commands and related usage information
        """

        if self.shell.commands == []:
            self.shell.say(u"No command has been found.")

        elif arguments in (None, ''):
            for key in self.shell.commands:
                command = self.shell.command(key)
                if not command.is_hidden:
                    self.shell.say(u"{} - {}".format(
                        command.keyword,
                        str(command.information_message)))

        else:
            command = self.shell.command(arguments)

            if command:
                self.shell.say(u"{} - {}".format(
                    command.keyword,
                    str(command.information_message)))
                self.shell.say(u"usage:")
                if command.usage_message:
                    self.shell.say(str(command.usage_message))
                else:
                    self.shell.say(str(command.keyword))

            else:
                self.shell.say(u"This command is unknown.")
