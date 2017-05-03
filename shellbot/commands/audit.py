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


class Audit(Command):
    """
    Checks and changes audit status
    """

    keyword = u'audit'
    information_message = u'Check and change audit status'
    usage_message = u'audit [on|off]'

    on_message = u'Chat interactions are currently audited.'
    off_message = u'Chat interactions are private. ' \
                  u'Auditing has not been activated.'
    already_on_message = u'Chat interactions are already audited.'
    already_off_message = u'Chat interactions are already private.'

    def execute(self, arguments=None):
        """
        Checks and changes audit status
        """
        if arguments == 'on':
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
