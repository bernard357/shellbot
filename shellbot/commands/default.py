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

    In this pseudo-command we handle all user input that is not a command.
    This is actually put to a queue, so that any process can pick it up
    and use it. Nevertheless, data is pushed to the queue only if some
    listeners can be sensed in the background. If this is not the case,
    a message is sent back to the user.

    For a listener to receive unmatched statements, the protocol works
    like this:

    * Check the ``bot.fan`` queue frequently

    * On each check, update the string ``fan.stamp`` in the context with the
      value of ``time.time()``. This will signal that you are around.

    In this object, we only check the value of ``fan.stamp`` from the context.
    If this fresh enough, then data is put to the ``bot.fan`` queue. Else
    a message is sent to the chat space.
    """

    keyword = u'*default'
    information_message = u'Handle unmatched command'
    is_hidden = True

    default_message = u"Sorry, I do not know how to handle '{}'"

    FRESH_DURATION = 0.5  # maximum amount of time for listener detection

    def execute(self, arguments):
        """
        Handles unmatched command

        Arguments provided should include all of the user input, including
        the first token that has not been recognised as a valid command.
        """
        if self.has_listeners():
            self.bot.fan.put(arguments)
        else:
            self.bot.say(self.default_message.format(arguments))

    def has_listeners(self):
        """
        Checks if the fan has listeners

        :return: True or False
        """
        elapsed = time.time() - self.bot.context.get('fan.stamp', 0)
        return elapsed < self.FRESH_DURATION
