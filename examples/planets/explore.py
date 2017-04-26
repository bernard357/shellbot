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

import time

from .mission import Mission

class Explore(Mission):
    """
    Explores a planet and comes back

    >>>command = Explore()
    >>>shell.load_command(command)

    """

    keyword = u'explore'
    information_message = u'Explore a planet and come back'
    usage_message = u'explore <destination>'

    action_begin_template = u"Exploring {}, this is interesting"
    action_begin_file = "http://static.ddmcdn.com/gif/blogs/6a00d8341bf67c53ef012877b0bdec970c-800wi.jpg"

    action_end_template = u"End of the exploration"

    def on_target_action(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.action_begin_template.format(self.target),
                     file=self.action_begin_file)
        time.sleep(5)
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.action_end_template.format(self.target))

