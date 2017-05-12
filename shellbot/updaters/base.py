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

from builtins import str
import logging
import os
from six import string_types
import sys
import time

from ..context import Context


class Updater(object):
    """
    Handles inbound messages

    Updaters are useful for proper logging or replication, or side
    storage, or achiving, of received messages.

    """

    def __init__(self,
                 bot=None,
                 **kwargs):
        """
        Handles inbound messages

        :param bot: the overarching bot
        :type bot: ShellBot

        Example::

            updater = Updater(bot=bot)
            updater.put(message)

        """
        self.bot = bot
        self.on_init(**kwargs)

    def on_init(self, **kwargs):
        """
        Handles extended initialisation parameters

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_init(self, prefix='secondary.space', **kwargs):
                ...

        """
        pass

    def put(self, message):
        """
        Processes one message

        :param message: inbound message
        :type message: dict

        The default behaviour is to write text to ``sys.stdout`` so it is easy
        to redirect the stream for any reason.
        """
        sys.stdout.write(self.format(message)+'\n')

    def format(self, message):
        """
        Prepares an outbound message

        :param message: an inbound message
        :type message: dict

        :return: outbound message
        :rtype: str

        This function adapts inbound messages to the appropriate
        format. It turns a dict with multiple attributes
        to a single string that can be saved in a log file.

        """
        person = message['personEmail']
        text = message['text']
        return str(u'{}: {}'.format(person, text))

