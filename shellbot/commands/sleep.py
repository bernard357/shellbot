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


class Sleep(Command):
    """
    Sleeps for a while
    """

    keyword = u'sleep'
    information_message = u'Sleep for a while'
    usage_message = u'sleep <n>'
    is_interactive = False
    is_hidden = True

    DEFAULT_DELAY = 1.0

    def execute(self, arguments):
        """
        Sleeps for a while
        """
        try:
            delay = float(arguments) if float(arguments) > 0.0 else 1.0
        except ValueError:
            delay = self.DEFAULT_DELAY
        time.sleep(delay)
