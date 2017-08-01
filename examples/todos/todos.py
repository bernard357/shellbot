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

class Todos(Command):
    """
    Displays the list of items to do

    >>>command = Todos(store=store)
    >>>shell.load_command(command)

    """

    keyword = u'todos'
    information_message = u'List items to do'
    list_header = u"On the todo list:"

    def execute(self, bot, arguments=None, **kwargs):
        """
        Displays the list of items to do
        """
        if self.engine.factory is None:
            raise AttributeError(u'Todo factory has not been initialised')

        if len(self.engine.factory.items):
            lines = []
            index = 1
            for item in self.engine.factory.items:
                lines.append(u"#{} {}".format(index, item))
                index += 1
            bot.say(self.list_header
                         + '\n- ' + '\n- '.join(lines))
        else:
            bot.say(u"Nothing to do yet.")
