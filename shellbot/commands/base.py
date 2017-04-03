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

    def __init__(self, shell):
        self.shell = shell
        self.context = shell.context

    def execute(self, arguments=None):
        """
        Executes this command

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        :return: True if the command has executed correctly, False otherwise
        :rtype: bool

        This function should report on progress by sending
        messages with one or multiple ``self.shell.say("Whatever response")``.

        """
        raise NotImplementedError()

    @property
    def keyword(self):
        """
        Retrieves the verb or token for this command

        :return: the verb or the token for this command, e.g., ``ignore``
        :rtype: str

        Example:
            >>>print(command.keyword)
            ignore
        """
        raise NotImplementedError()

    @property
    def information_message(self):
        """
        Retrieves basic information for this command

        :return: the one-line information message for this command
        :rtype: str

        Example:
            >>>print(command.information_message)
            Ignores the current alert.
        """
        raise NotImplementedError()

    @property
    def usage_message(self):
        """
        Retrieves usage information for this command

        :return: the text that explain how to use this command
        :rtype: str or ``None``

        Example:
            >>>print(command.usage_message)
            ["`ignore (last|current) XhYm`",
             "Ignores an alert for X hours and Y minutes.",
             "Selectable whether this ignores the current or last alert."]
        """
        return None

    @property
    def is_interactive(self):
        """
        Checks if this command should be processed interactively or not

        :return:
        :rtype: bool

        Example:
            >>>print(command.is_interactive)
            True

        Interactive commands are executed immediately, while non-interactive
        commands are executed in the background
        """
        return True

    @property
    def is_hidden(self):
        """
        Ensures that this command appears in help

        :return:
        :rtype: bool

        Example:
            >>>print(command.is_hidden)
            False
        """
        return False

