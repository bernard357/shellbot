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


class Close(Command):
    """
    Closes the room

    >>>close = Close(bot=bot)
    >>>shell.load_command(close)

    """
    keyword = 'close'
    information_message = u"Close this room"

    def execute(self, arguments=None):
        self.bot.say(self.information_message)
        self.bot.stop()
        self.bot.dispose()
