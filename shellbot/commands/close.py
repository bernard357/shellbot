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
    Closes the space

    >>>close = Close(engine=my_engine)
    >>>shell.load_command(close)

    """
    keyword = 'close'
    information_message = u"Close this space"

    in_direct = False  # do not allow command to close a direct channel

    def execute(self, bot, arguments=None, **kwargs):
        """
        Closes the space

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        This function should report on progress by sending
        messages with one or multiple ``bot.say("Whatever response")``.

        """
        bot.say("Closing this channel")
        bot.dispose()
