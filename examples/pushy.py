#!/usr/bin/env python
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

"""
Push a button to start interactions

In this example an external event is captured via a web request. This creates
a collaborative place where multiple persons can participate.

"""

import logging
import os
from multiprocessing import Process, Queue
from Queue import Empty
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import ShellBot, Context, Command, Server, Notify, Wrapper
Context.set_logger()

#
# load configuration
#

settings = {

    'bot': {
        'on_start': 'Welcome to this on-demand collaborative room',
        'on_stop': 'Bot is now quitting the room, bye',
    },

    'spark': {
        'room': 'On-demand collaboration',
        'moderators': 'bernard.paques@dimensiondata.com',
    },

    'server': {
        'url': 'http://ceb1bfec.ngrok.io',
        'trigger': '/trigger',
        'hook': '/hook',
        'binding': '0.0.0.0',
        'port': 8080,
    },

    'process': {
        'states': ['start', 'escalation', 'end'],
        'initial.state': 'start',
    },


}

context = Context(settings)
context.check('server.trigger', '/trigger')
context.check('server.hook', '/hook')

#
# create a bot and load commands
#

bot = ShellBot(context=context, check=True)

from linear.state import State
from linear.next import Next

bot.load_commands([State(), Next()])

#
# a queue of events between the web server and the bot
#

queue = Queue()

#
# create a web server to receive trigger
#

server = Server(context=context, check=True)

server.add_route(Notify(route=context.get('server.trigger'),
                        queue=queue,
                        notification='click'))

server.add_route(Wrapper(route=context.get('server.hook'),
                         callable=bot.get_hook()))

#
# delay the creation of a room until we receive some trigger
#

class Trigger(object):

    def __init__(self, context, queue, bot):
        self.context = context
        self.queue = queue if queue else Queue()
        self.bot = bot

    def work(self):
        logging.info(u"Waiting for trigger")

        try:
            self.context.set('trigger.counter', 0)
            while self.context.get('general.switch', 'on') == 'on':
                try:
                    item = self.queue.get(True, 0.1)
                    if isinstance(item, Exception):
                        break
                    counter = self.context.increment('trigger.counter')
                    self.process(item, counter)
                except Empty:
                    pass

        except KeyboardInterrupt:
            pass

    def process(self, item, counter):
        logging.info(u'Trigger {} {}'.format(item, counter))

        if counter == 1:
            self.bot.bond(reset=True)
            self.bot.hook()

        else:
            self.bot.say(u'{} {}'.format(item, counter))

#
# launch multiple processes to do the job
#

trigger = Trigger(context, queue, bot)
p = Process(target=trigger.work)
p.start()

bot.start()
server.run()

#
# clean the room
#

bot.stop()
bot.space.dispose(context.get('spark.room'))