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
from multiprocessing import Process, Queue
import time


class Rocket(object):
    """
    Flies around
    """

    home_departure_template = u"Departing to {}"
    target_approach_template = u"Approaching {}"
    target_landed_template = u"Landed on {}"
    target_departure_template = u"Now flying back to {}"
    home_approach_template = u"Approaching {}"
    home_landed_template = u"Landed, ready for next mission"

    explore_begin_template = u"Exploring {}, this is interesting"
    explore_begin_file = "http://www.dummysoftware.com/mars/lander.jpg"
    explore_end_template = u"End of the exploration"

    blast_begin_template = u"Blasting {}, nobody will survive"
    blast_end_template = u"{} has been entirely blasted"
    blast_end_file = "http://blogs.discovermagazine.com/badastronomy/files/2012/07/nuke_castleromeo.jpg"

    counter = 0

    def __init__(self, bot, inbox=None):
        """
        Flies around

        :param bot: the bot associated to this rocket
        :type bot: ShellBot

        :param inbox: queue to get commands
        :type inbox: Queue

        """
        self.bot = bot
        self.inbox = inbox if inbox else Queue()

    def go(self, action, planet):
        """
        Engages a new mission
        """
        if not self.bot.recall('rocket.busy', False):
            self.bot.say(u"Ok, working on it")
        else:
            self.bot.say(u"Ok, will work on it as soon as possible")
        self.inbox.put((action, planet))

    def start(self):
        """
        Starts the working process

        :return: either the process that has been started, or None

        This function starts a separate daemonic process to work
        in the background.
        """
        p = Process(target=self.run)
        p.daemon = True
        p.start()
        return p

    def run(self):
        """
        Continuously processes commands

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in the background, like
        in the following example::

            rocket = Rocket(bot=my_bot)
            handle = rocket.start()

            ...

            handle.join()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            inbox.put(None)

        """
        logging.info(u"Starting rocket")

        self.counter = 0
        self.bot.remember('rocket.busy', False)

        try:
            while self.bot.engine.get('general.switch', 'on') == 'on':

                if self.inbox.empty():
                    time.sleep(0.005)
                    continue

                try:
                    item = self.inbox.get(True, 0.1)
                    if item is None:
                        break

                    self.bot.remember('rocket.busy', True)
                    self.process(item)
                    self.bot.remember('rocket.busy', False)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        finally:
            logging.info(u"Rocket has been stopped")

    def process(self, item):
        """
        Processes one action

        :param item: the action to perform
        :type item: list or tuple

        Example actions::

            rocket.process(item=('explore', 'Venus'))

            rocket.process(item=('blast', 'Mars'))

        """
        (verb, planet) = item

        assert verb in ('explore', 'blast')
        planet = planet.capitalize()

        logging.debug(u"Rocket is working on '{} {}'".format(verb, planet))

        items = self.bot.recall('planets', [])
        if planet not in items:
            self.bot.say(u"Planet '{}' is unknown".format(planet))
            return

        self.counter += 1

        self.on_home_departure(planet)
        self.on_target_approach(planet)
        self.on_target_landing(planet)
        if verb == 'blast':
            self.on_target_blast(planet)
        else:
            self.on_target_explore(planet)
        self.on_target_departure('Earth')
        self.on_home_approach('Mother Earth')
        self.on_home_landing('Mother Earth')

    def on_home_departure(self, planet, duration=9):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.home_departure_template.format(planet))
        time.sleep(duration)

    def on_target_approach(self, planet, duration=3):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.target_approach_template.format(planet))
        time.sleep(duration)

    def on_target_landing(self, planet, duration=1):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.target_landed_template.format(planet))
        time.sleep(duration)

    def on_target_explore(self, planet, duration=2):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.explore_begin_template.format(planet),
                     file=self.explore_begin_file)
        time.sleep(duration)

        self.bot.say(u"#{} - ".format(self.counter)
                     + self.explore_end_template.format(planet))
        time.sleep(1)

    def on_target_blast(self, planet, duration=2):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.blast_begin_template.format(planet))
        time.sleep(duration)

        items = self.bot.recall('planets', [])
        items.remove(planet)
        self.bot.remember('planets', items)

        self.bot.say(u"#{} - ".format(self.counter)
                     + self.blast_end_template.format(planet),
                     file=self.blast_end_file)
        time.sleep(1)

    def on_target_departure(self, planet, duration=9):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.target_departure_template.format(planet))
        time.sleep(duration)

    def on_home_approach(self, planet, duration=3):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.home_approach_template.format(planet))
        time.sleep(duration)

    def on_home_landing(self, planet, duration=1):
        self.bot.say(u"#{} - ".format(self.counter)
                     + self.home_landed_template.format(planet))
        time.sleep(duration)
