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
from shellbot.events import Message


class Audit(Command):
    """
    Checks and changes audit status

    In essence, audit starts with the capture of information in real-time,
    and continues with the replication of information.

    A typical use case is the monitoring of interactions happening in a channel,
    for security reasons, for compliancy or, simply speaking, for
    traceability.

    Audit can be suspended explicitly by channel participants. This allows for
    some private exchanges that are not audited at all. However, then command
    is put in the audit log itself, so that people can be queried afterwards
    on their private interactions.
    If the parameter ``off_duration`` is set, then it is used by a watchdog
    to restart auditing. Else it is up to channel participants to activate or
    to de-activate auditing, at will.

    The command itself allows for suspending or restarting the audit process.
    When audit has been activated in a channel, the attribute
    ``audit.switch.<channel_id>`` is set to ``on`` in the context. This can be
    checked by the observer while handling inbound records.

    The audit has to be armed beforehand, and this is checked from the context
    attribute ``audit.has_been_armed``. In normal cases, audit is armed from
    the underlying space by setting this attribute to True.

    """

    keyword = u'audit'
    information_message = u'Check and change audit status'
    usage_message = u'audit [on|off]'

    in_direct = False  # do not audit 1:1 interactions

    disabled_message = u'Audit has not been enabled.'

    on_message = u'Chat interactions are currently audited.'
    off_message = u'Chat interactions are not audited.'
    already_on_message = u'Chat interactions are already audited.'
    already_off_message = u'Chat interactions are already private.'

    off_duration = 60  # after this time off, back to auditing on
    temporary_off_message = u"Please note that auditing will restart after {}"

    def execute(self, bot, arguments=None, **kwargs):
        """
        Checks and changes audit status

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: either 'on' or 'off'
        :type arguments: str

        """
        if not self.has_been_enabled:
            bot.say(self.disabled_message)

        elif arguments == 'on':
            self.audit_on(bot)

        elif arguments =='off':
            self.audit_off(bot)

        elif arguments in (None, ''):
            self.audit_status(bot)

        else:
            bot.say(u"usage: {}".format(self.usage_message))

    def audit_on(self, bot):
        """
        Activates audit mode

        :param bot: The bot for this execution
        :type bot: Shellbot

        """
        label = 'audit.switch.{}'.format(bot.id)
        logging.debug(u"- activating audit mode for {}".format(label))
        if self.engine.get(label, 'off') == 'on':
            bot.say(self.already_on_message)
        else:
            self.engine.set(label, 'on')
            bot.say(self.on_message)

    def audit_off(self, bot):
        """
        Activates private mode

        :param bot: The bot for this execution
        :type bot: Shellbot

        """
        label = 'audit.switch.{}'.format(bot.id)
        logging.debug(u"- de-activating audit mode for {}".format(label))
        if self.engine.get(label, 'off') == 'on':
            self.engine.set(label, 'off')
            bot.say(self.off_message)
            self.on_off(bot)
        else:
            bot.say(self.already_off_message)

    def audit_status(self, bot):
        """
        Reports on audit status

        :param bot: The bot for this execution
        :type bot: Shellbot

        """
        label = 'audit.switch.{}'.format(bot.id)
        if self.engine.get(label, 'off') == 'on':
            bot.say(self.on_message)
        else:
            bot.say(self.off_message)

    @property
    def has_been_enabled(self):
        """
        Are we ready for auditing or not?

        :rtype: bool
        """
        return self.engine.get('audit.has_been_armed', False)

    def on_init(self):
        """
        Registers callback from bot
        """
        self.engine.register('bond', self)

    def on_bond(self, bot):
        """
        Activates audit when a bot joins a channel
        """
        if bot.channel.is_group:
            logging.info(u"Activating real-time audit")
            self.audit_on(bot)

    def on_off(self, bot):
        """
        Triggers watchdog when audit is disabled
        """
        if self.off_duration and self.off_duration > 0:

            bot.say(
                self.temporary_off_message.format(
                    str(self.off_duration)+' seconds'))

            logging.debug(u"- triggering watchdog timer")
            label = 'audit.switch.{}'.format(bot.id)
            t = Timer(self.off_duration, self.watchdog, [bot])
            t.start()

    def watchdog(self, bot):
        """
        Ensures that audit is restarted
        """
        logging.debug(u"Watchdog is checking audit status")
        label = 'audit.switch.{}'.format(bot.id)
        if self.engine.get(label, 'off') == 'off':
            logging.debug(u"- restarting audit")
            self.audit_on(bot)
