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
from multiprocessing import Queue
import os
from six import string_types
import sys
import time

from .base import Updater


class QueueUpdater(Updater):
    """
    Writes inbound events to a queue

    This updater serializes events and write them to a queue.

    An event may be a Message, an Attachment, a Join or Leave notification,
    or any other Event.

    Updaters expose a filtering function that can be connected to the
    inbound flow of events handled by the Listener.

    Example::

        updater = QueueUpdater(queue=Queue())
        listener = Listener(filter=updater.filter)

    Of course, some process has to grab content from `updater.queue`
    afterwards.
    """

    def on_init(self, queue=None, **kwargs):
        """
        Writes inbound events to a queue
        """
        self.queue = queue if queue else Queue()

    def put(self, event):
        """
        Processes one event

        :param event: inbound event
        :type event: Event or Message or Attachment or Join or Leave

        This function serializes the event and write it to a queue.
        """
        self.queue.put(str(event))
