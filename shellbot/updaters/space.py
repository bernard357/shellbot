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

import logging
from multiprocessing import Queue

from ..context import Context
from ..speaker import Speaker
from .base import Updater
from ..spaces import SparkSpace



class SpaceUpdater(Updater):
    """
    Replicates messages to a secondary space
    """

    def on_init(self, space=None, speaker=None, **kwargs):
        """
        Replicates messages to a secondary space

        :param space: the target space to use (optional)
        :type space: Space

        :param speaker: the speaker instance to use (optional)
        :type speaker: Speaker

        Parameters are provided mainly for test injection.
        """

        # create a secondary room
        #
        self.space = space if space else SparkSpace(bot=self)

        self.space.connect()

        title = u"{} - {}".format(
            self.space.configured_title(), u"Audited content")

        self.space.bond(title=title)

        # speak incoming updates
        #
        self.context = Context()
        self.mouth = Queue()

        self.speaker = speaker if speaker else Speaker(bot=self)
        self.speaker.run()

    def put(self, message):
        """
        Processes one message

        :param message: inbound message
        :type message: dict

        With this class a string representation of the received item
        is forwarded to the speaker queue of a chat space.
        """
        self.mouth.put(self.format(message))

