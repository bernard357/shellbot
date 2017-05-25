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
from threading import Timer

from .base import Command
from shellbot.updaters import Updater


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
    off_message = u'Chat interactions are not audited.'
    already_on_message = u'Chat interactions are already audited.'
    already_off_message = u'Chat interactions are already private.'

    off_duration = 60  # after this time off, back to auditing on
    temporary_off_message = u"Please note that auditing will restart after {}"

    updater = None
    updater_ruler = u"<br >"

    _armed = False  # for tests only

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
            self.on_off()
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

        :rtype: bool
        """
        if self._armed:
            return True

        if self.updater is None:
            return False

        if self.bot.listener.filter != self.filter:
            return False

        return True

    def on_init(self):
        """
        Registers callback from bot
        """
        logging.debug(u"- registering audit to bot 'run'")
        self.bot.register('start', self)

    def on_start(self):
        """
        Reacts on bot start
        """
        self.bot.say('Tuning audit')
        self.execute('on')

    def on_off(self):
        """
        Triggers watchdog when audit is disabled
        """
        if self.off_duration and self.off_duration > 0:

            self.bot.say(
                self.temporary_off_message.format(
                    str(self.off_duration)+' seconds'))

            logging.debug(u"- triggering watchdog timer")
            t = Timer(self.off_duration, self.watchdog)
            t.start()

    def watchdog(self):
        """
        Ensures that audit is restarted
        """
        logging.debug(u"Watchdog is cheking audit status")
        if self.bot.context.get('audit.switch', 'off') == 'off':
            logging.debug(u"- restarting audit")
            self.audit_on()

    def filter(self, event):
        """
        Filters events handled by listener

        :param event: an event received by listener
        :type event: Event or Message or Attachment or Join or Leave, etc.

        :return: a filtered event

        This function implements the actual auditing of incoming events.
        """
        logging.debug(u"- filtering a {} event".format(event.type))
        try:
            if self.bot.context.get('audit.switch', 'off') == 'on':
                logging.debug(u"- {}".format(str(event)))
                self.updater.put(event)
            else:
                logging.debug(u"- audit has not been switched on")
        finally:
            return event
