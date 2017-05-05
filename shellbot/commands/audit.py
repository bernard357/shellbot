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
from multiprocessing import Process, Queue

from .base import Command
from ..spaces import SparkSpace


class Audit(Command):
    """
    Checks and changes audit status
    """

    keyword = u'audit'
    information_message = u'Check and change audit status'
    usage_message = u'audit [on|off]'

    disabled_message = u'Audit has not been enabled.'

    on_message = u'Chat interactions are currently audited.'
    off_message = u'Chat interactions are private. ' \
                  u'Auditing has not been activated.'
    already_on_message = u'Chat interactions are already audited.'
    already_off_message = u'Chat interactions are already private.'

    _armed = False
    space = None
    mouth = None

    def execute(self, arguments=None):
        """
        Checks and changes audit status

        :param arguments: either 'on' or 'off'
        :type arguments: str

        """
        if self.armed == False:
            self.bot.say(self.disabled_message)

        elif arguments == 'on':
            self.audit_on()

        elif arguments =='off':
            self.audit_off()

        elif arguments in (None, ''):
            self.audit_status()

        else:
            self.bot.say(u"usage: {}".format(self.usage_message))

    def audit_on(self):
        """
        Activates audit mode
        """
        if self.bot.context.get('audit.switch', 'off') == 'on':
            self.bot.say(self.already_on_message)
        else:
            self.bot.context.set('audit.switch', 'on')
            self.bot.say(self.on_message)

    def audit_off(self):
        """
        Activates private mode
        """
        if self.bot.context.get('audit.switch', 'off') == 'on':
            self.bot.context.set('audit.switch', 'off')
            self.bot.say(self.off_message)
        else:
            self.bot.say(self.already_off_message)

    def audit_status(self):
        """
        Reports on audit status
        """
        if self.bot.context.get('audit.switch', 'off') == 'on':
            self.bot.say(self.on_message)
        else:
            self.bot.say(self.off_message)

    def arm(self, space=None, speaker=None):
        """
        Arms the auditing function

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
            self.bot.context.get('spark.room', 'Test'), u"Audited content")

        self.space.bond(title=title)

        # speak incoming updates
        #
        self.mouth = Queue()

        self.speaker = speaker if speaker else Speaker(bot=self)
        self.speaker.run()

        # audit incoming updates
        #
        self.bot.listener.filter = self.filter

    @property
    def armed(self):
        """
        Are we ready for auditing or not?
        """
        if self._armed:
            return True

        if self.space is None:
            return False

        if self.mouth is None:
            return False

        if self.bot.listener.filter != self.filter:
            return False

        return True

    def filter(self, item):
        """
        Filters items handled by listener

        :param item: an item received by listener
        :type item: dict

        :return: a filtered item

        This function implements the actual auditing of incoming messages.
        """
        try:
            self.mouth.put(self.format(item))
        finally:
            return item

    def format(self, item):
        """
        Prepares an outbound message

        :param item: an inbound message
        :type item: dict

        :return: outbound message
        :rtype: str or Message

        """
        person = item['personEmail']
        text = item['text']
        return u'{}: {}'.format(person, text)

