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

class Done(Command):
    """
    Archives an item from the todo list

    >>>command = Done()
    >>>shell.load_command(command)

    """

    keyword = u'done'
    information_message = u'Archive an item from the todo list'
    usage_message = u'done [#<n>]'

    def execute(self, bot, arguments=None, **kwargs):
        """
        Archives an item from the todo list
        """
        if self.engine.factory is None:
            raise AttributeError(u'Todo factory has not been initialised')

        if arguments in (None, ''):
            index = 1
        else:
            index = self.engine.factory.parse(arguments)

        if index is None:
            bot.say(u"usage: {}".format(self.usage_message))
            return

        if index > len(self.engine.factory.items):
            bot.say(u"Nothing to do yet.")

        else:
            old_item = self.engine.factory.read(index)
            self.engine.factory.complete(index)

            next_item = self.engine.factory.read()

            for bot in self.engine.enumerate_bots():
                bot.say(u"Archived: {}".format(old_item))

                if next_item:
                    bot.say(u"Coming next: {}".format(next_item))
                else:
                    bot.say(u"Nothing to do yet.")
