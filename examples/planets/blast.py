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
import time

from .mission import Mission

class Blast(Mission):
    """
    Blasts a planet and comes back

    >>>command = Blast()
    >>>shell.load_command(command)

    """

    keyword = u'blast'
    information_message = u'Blast a planet and come back'
    usage_message = u'blast <destination>'

    action_begin_template = u"Blasting {}, nobody will survive"
    action_end_template = u"{} has been entirely blasted"
    action_end_file = "http://blogs.discovermagazine.com/badastronomy/files/2012/07/nuke_castleromeo.jpg"

    def on_target_action(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.action_begin_template.format(self.target))
        time.sleep(1)

        items = self.bot.context.get('planets.items', [])
        items.remove(self.target)
        self.bot.context.set('planets.items', items)

        self.bot.say(u"#{} - ".format(self.counter)
                     + self.action_end_template.format(self.target),
                     file=self.action_end_file)
