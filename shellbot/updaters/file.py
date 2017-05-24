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

from .base import Updater


class FileUpdater(Updater):
    """
    Writes inbound events to a file

    This updater serializes events and write JSON records to a flat file.

    An event may be a Message, an Attachment, a Join or Leave notification,
    or any other Event.

    Updaters expose a filtering function that can be connected to the
    inbound flow of events handled by the Listener.

    Example::

        updater = FileUpdater(path='/var/log/my_app.log')
        listener = Listener(filter=updater.filter)

    """

    def on_init(self, path=None, **kwargs):
        """
        Writes inbound events to a file
        """
        self.path = path

    def get_path(self):
        """
        Provides the path to the target file

        :rtype: str
        """
        if self.path in (None, ''):
            return self.bot.get('file.updater.path', '/var/log/shellbot.log')

        return self.path

    def on_bond(self):
        """
        Creates path on space bonding
        """
        path = os.path.dirname(self.get_path())
        if not os.path.exists(path):
            os.makedirs(path)

    def put(self, event):
        """
        Processes one event

        :param event: inbound event
        :type event: Event or Message or Attachment or Join or Leave

        The function serializes the event and write it to a file.
        """
        path = self.get_path()
        logging.debug("- updating {}".format(path))

        if os.path.exists(path):
            mode = 'a'
        else:
            mode = 'w'

        with open(path, mode) as handle:
            handle.write(str(event)+'\n')
