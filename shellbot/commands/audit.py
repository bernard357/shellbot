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
from ..updaters import Updater


class Audit(Command):
    """
    Checks and changes audit status

    In essence, audit starts with the capture of information in real-time,
    and continues with the replication of information.

    A typical use case is the monitoring of interactions happening in a space,
    for security reasons or for compliancy.

    The command Audit() has to be armed beforehand, meaning that it is
    provided with a callable function that can receive updates, and that
    it hooks the listener to filter all inbound traffic.

    The command itself allows for suspending or restarting the audit process.


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
    updater = None

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

    def arm(self, updater):
        """
        Arms the auditing function

        :param updater: the function to be used on each update
        :type updater: callable

        """
        assert updater is not None
        self.updater = updater
        self.bot.listener.filter = self.filter

    @property
    def armed(self):
        """
        Are we ready for auditing or not?
        """
        if self._armed:
            return True

        if self.updater is None:
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
            if self.bot.context.get('audit.switch', 'off') == 'on':
                self.updater.put(item)
        finally:
            return item
