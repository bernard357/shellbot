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

class Next(Command):
    """
    Displays the next item to do

    >>>command = Next(store=store)
    >>>shell.load_command(command)

    """

    keyword = u'next'
    information_message = u'Display next item to do'

    def execute(self, arguments=None):
        """
        Displays the next item to do
        """
        if self.bot.factory is None:
            raise AttributeError(u'Todo factory has not been initialised')

        item = self.bot.factory.read()
        if item is not None:
            self.bot.say(u"Coming next: {}".format(item))
        else:
            self.bot.say(u"Nothing to do yet.")
