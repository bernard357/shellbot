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

class Todo(Command):
    """
    Creates or updates an item to do

    >>>command = Todo(store=store)
    >>>shell.load_command(command)

    """

    keyword = u'todo'
    information_message = u'Append an item to the todo list, or change it'
    usage_message = u'todo [#n] <something to do>'
    store = None

    def execute(self, arguments=None):
        """
        Creates or updates an item to do
        """
        if self.store is None:
            raise AttributeError(u'Todo store has not been initialised')

        if arguments in (None, ''):
            self.bot.say(u"usage: {}".format(self.usage_message))
            return

        index = self.store.parse(arguments)
        if index is None and arguments[0] == '#':
            self.bot.say(u"usage: {}".format(self.usage_message))
            return

        if index is None:
            self.store.create(arguments)
            self.bot.say(u"#{} {}".format(len(self.store.items), arguments))
        else:
            (dummy, arguments) = arguments.split(' ', 1)
            self.store.update(index, arguments)
            self.bot.say(u"#{} {}".format(index, arguments))
