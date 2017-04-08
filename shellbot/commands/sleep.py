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

from base import Command

class Sleep(Command):
    """
    Sleeps for a while
    """

    def execute(self, verb, arguments):
        """
        Sleeps for a while
        """
        try:
            delay = int(arguments) if int(arguments) > 0 else 1
        except ValueError:
            delay = 1
        time.sleep(delay)
        return True

    @property
    def keyword(self):
        """
        Retrieves the verb or token for this command
        """
        return 'sleep'

    @property
    def information_message(self):
        """
        Retrieves basic information for this command
        """
        return 'Sleeps for a while.'

    @property
    def usage_message(self):
        """
        Retrieves usage information for this command
        """
        return 'sleep <n>'

    @property
    def is_interactive(self):
        """
        Checks if this command should be processed interactively or not
        """
        return False

    @property
    def is_hidden(self):
        """
        Ensures that this command does not appear in help
        """
        return True
