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

class Empty(Command):
    """
    Handles empty command
    """

    def execute(self, *args):
        """
        Handles empty command
        """
        if not hasattr(self, 'help_command'):
            self.help_command = self.shell.command('help')

        if self.help_command is None:
            return False

        self.help_command.execute('help')
        return True

    @property
    def keyword(self):
        """
        Retrieves the verb or token for this command
        """
        return '*empty'

    @property
    def information_message(self):
        """
        Retrieves basic information for this command
        """
        return 'Handles empty command.'

    @property
    def usage_message(self):
        """
        Retrieves usage information for this command
        """
        return None

    @property
    def is_hidden(self):
        """
        Ensures that this command appears in help
        """
        return True
