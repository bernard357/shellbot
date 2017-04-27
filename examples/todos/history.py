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

from shellbot import Command

class History(Command):
    """
    Displays the list of completed items

    >>>command = History(store=store)
    >>>shell.load_command(command)

    """

    keyword = u'history'
    information_message = u'List archived items'
    list_header = u"Items that have been archived:"

    def execute(self, arguments=None):
        """
        Displays the list of completed items
        """
        if self.bot.factory is None:
            raise AttributeError(u'Todo factory has not been initialised')

        if len(self.bot.factory.archive):
            self.bot.say(self.list_header
                         + '\n- ' + '\n- '.join(self.bot.factory.archive))
        else:
            self.bot.say(u"No item has been completed yet.")
