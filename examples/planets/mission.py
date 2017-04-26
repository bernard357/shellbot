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

from shellbot import Command

class Mission(Command):
    """
    Flights to a planet and comes back

    >>>command = Mission()
    >>>shell.load_command(command)

    """

    keyword = u'mission'
    information_message = u'Flight to a planet and come back'
    usage_message = u'mission <destination>'
    is_interactive = False

    home_departure_template = u"Departing to {}"
    target_approach_template = u"Approaching {}"
    target_landed_template = u"Landed on {}"
    target_departure_template = u"Now flying back to Earth"
    home_approach_template = u"Approaching Mother Earth"
    home_landed_template = u"Landed, ready for next mission"

    counter = 0

    def execute(self, arguments=None):
        """
        Flights to a planet and comes back
        """

        if arguments in (None, ''):
            self.bot.say(u"usage: {}".format(self.usage_message))
            return

        items = self.bot.context.get('planets.items', [])
        if arguments.capitalize() not in items:
            self.bot.say(u"Planet '{}' is unknown".format(arguments))
            return

        Mission.counter += 1
        self.target = arguments.capitalize()

        self.on_home_departure()
        time.sleep(9)

        self.on_target_approach()
        time.sleep(3)

        self.on_target_landing()

        self.on_target_action()

        self.on_target_departure()
        time.sleep(9)

        self.on_home_approach()
        time.sleep(3)

        self.on_home_landing()

    def on_home_departure(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.home_departure_template.format(self.target))

    def on_target_approach(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.target_approach_template.format(self.target))

    def on_target_landing(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.target_landed_template.format(self.target))

    def on_target_action(self):
        pass

    def on_target_departure(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.target_departure_template.format(self.target))

    def on_home_approach(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.home_approach_template.format(self.target))

    def on_home_landing(self):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.home_landed_template.format(self.target))
        time.sleep(1)
