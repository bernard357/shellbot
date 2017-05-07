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

Then following commands are available from the bot:

- command: next
- response describes the name and characteristics of new state

- command: state
- response describes current state

- command: close
- responses describes the proper archiving of the room


Multiple questions are adressed in this example:

- How to create a room on some external event? Here we wait for a link to be
  triggered over the internet. This can done directly from the command line
  with CURL, from a web browser, or from a button connected to the internet, or
  from an application on a mobile device. When this occurs, a room is created,
  moderators and participants are added, and people can interact immediately.
  Look at the class ``Trigger`` below, and at the bottom of the script, to see
  how this is implemented.

- How to implement a linear process? The typical use case is to let joining
  people interact in the room, then involve some support experts, then
  call stakeholders for a decision. These are reflected in the chat room
  with commands ``state`` and ``next``. Related code is in the ``steps``
  subdirectory.


A typical dialog could be like the following::

    > shelly next

    New state: Level 1 - Initial capture of information
    If you are on the shop floor:
    - Take a picture of the faulty part
    - Describe the issue in the chat box

    As a Stress engineer, engage with shop floor and ask questions. To engage
    with the design team, type next in the chat box.

    > shelly next

    New state: Level 2 - Escalation to technical experts

    ...


To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHAT_ROOM_MODERATORS`` - You have at least your e-mail address
- ``CHAT_TOKEN`` - Received from Cisco Spark when you register your bot
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHAT_ROOM_MODERATORS="alice@acme.com"
    export CHAT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python pushy.py


"""

import logging
#import os
from multiprocessing import Process, Queue
import time

from shellbot import ShellBot, Context, Server, Notify, Wrap
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
        'moderators': '$CHAT_ROOM_MODERATORS',
        'token': '$CHAT_TOKEN',
    },

    'server': {
        'url': '$SERVER_URL',
        'trigger': '/trigger',
        'hook': '/hook',
        'binding': '0.0.0.0',
        'port': 8080,
    },

    'process.steps': [

        {
            'label': u'Level 1',
            'message': u'Initial capture of information',
            'markdown': u'If you are on the shop floor:\n'
                + u'* Take a picture of the faulty part\n'
                + u'* Describe the issue in the chat box\n'
                + u'\n'
                + u'As a Stress engineer, engage with shop floor and ask questions.'
                + u' To engage with the design team, type **next** in the chat box.'
        },

        {
            'label': u'Level 2',
            'message': u'Escalation to technical experts',
            'moderators': 'guillain@gmail.com',
        },

        {
            'label': u'Level 3',
            'message': u'Escalation to decision stakeholders',
            'participants': 'bernard.paques@laposte.net',
        },

        {
            'label': u'Terminated',
            'message': u'Process is closed, yet conversation can continue',
        },

    ],

}

context = Context(settings)
context.check('server.trigger', '/trigger')
context.check('server.hook', '/hook')

#
# create a bot and load commands
#

bot = ShellBot(context=context, configure=True)

from shellbot.commands import Close
bot.load_command(Close())  # allow space deletion from the chat

from steps import StepsFactory, Steps
bot.steps = Steps(context=context, configure=True)
bot.load_commands(StepsFactory.commands())

#
# a queue of events between the web server and the bot
#

queue = Queue()

#
# create a web server to receive trigger
#

server = Server(context=context, check=True)

server.add_route(Notify(queue=queue,
                        notification='click',
                        route=context.get('server.trigger')))

server.add_route(Wrap(callable=bot.get_hook(),
                      route=context.get('server.hook')))

#
# delay the creation of a room until we receive some trigger
#

class Trigger(object):

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, bot, queue):
        self.bot = bot
        self.queue = queue if queue else Queue()

    def work(self):
        logging.info(u"Waiting for trigger")

        try:
            self.bot.context.set('trigger.counter', 0)
            while self.bot.context.get('general.switch', 'on') == 'on':

                if self.queue.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.queue.get(True, self.EMPTY_DELAY)
                    if isinstance(item, Exception):
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

    def process(self, item):

        counter = self.bot.context.increment('trigger.counter')
        logging.info(u'Trigger {} {}'.format(item, counter))

        if counter == 1:
            self.bot.bond(reset=True)
            self.bot.space.on_run()
            self.bot.hook()

        else:
            self.bot.say(u'{} {}'.format(item, counter))

#
# launch multiple processes to do the job
#

bot.start()

trigger = Trigger(bot, queue)
p = Process(target=trigger.work)
p.daemon = True
p.start()

server.run()
