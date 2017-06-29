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


class Update(Command):
    """
    Update input data
    """

    keyword = u'update'
    information_message = u'Update input content'

    no_arg = u'Thanks to provide the key and the data'
    no_input = u'There is nothing to update, input is empty'
    ok_msg = u'Update successfuly done'

    def execute(self, arguments):
        """
        Update input data
        """
        if arguments in (None, ''):
            self.bot.say(self.no_arg, content=self.no_arg)
            return

        input = self.bot.recall('input')
        if input in (None, {}):
            self.bot.say(self.no_input)
            return

        arg = arguments.split(' ', 1)[1] # to keep the full line
        arg = arg.replace(" ", "")        
        key = arguments.replace(arg,'')
        key = key.replace(" ", "")
        self.bot.update('input', key, arg)
        self.bot.say(self.ok_msg)


