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

- command: step
- response describes the name and characteristics of new state

- command: state
- response describes current state

- command: close
- responses describes the proper archiving of the channel


Multiple questions are adressed in this example:

- How to create a channel on some external event? Here we wait for a link to be
  triggered over the internet. This can done directly from the command line
  with CURL, from a web browser, or from a button connected to the internet, or
  from an application on a mobile device. When this occurs, a channel is
  created, participants are added, and people can interact immediately.
  Look at the class ``Handler`` below to see how this is implemented.

- How to implement a linear process? The typical use case is to let joining
  people interact in the channel, then involve some support experts, then
  call stakeholders for a decision. This is reflected in the chat channel
  with command ``step``.


A typical dialog could be like the following::

    > shelly step

    New state: Level 1 - Initial capture of information
    If you are on the shop floor:
    - Take a picture of the faulty part
    - Describe the issue in the chat box

    As a Stress engineer, engage with shop floor and ask questions. To engage
    with the design team, type next in the chat box.

    > shelly step

    New state: Level 2 - Escalation to technical experts

    ...


To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHANNEL_DEFAULT_PARTICIPANTS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHANNEL_DEFAULT_PARTICIPANTS="alice@acme.com"
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python pushy.py


"""

import logging
from multiprocessing import Process, Queue
import time

from shellbot import Engine, Context, Server, Notifier, Wrapper
from shellbot.machines import Steps

Context.set_logger()

settings = {

    'bot': {
        'on_enter': 'Welcome to this on-demand collaborative room',
        'on_exit': 'Bot is now quitting the room, bye',
    },

    'spark': {
        'room': 'On-demand collaboration',
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
            'content': (u'If you are on the shop floor:\n'
                        u'* Take a picture of the faulty part\n'
                        u'* Describe the issue in the chat box\n'
                        u'\n'
                        u'As a Stress engineer, '
                        u'engage with shop floor and ask questions.'
                        u' To engage with the design team, '
                        u'type **step** in the chat box.')
        },

        {
            'label': u'Level 2',
            'message': u'Escalation to technical experts',
            'participants': 'guillain@gmail.com',
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


class MyFactory(object):  # provide state machine to group channels

    def __init__(self, steps):
        self.steps = steps

    def get_machine(self, bot):
        if bot.channel.is_group:
            return Steps(bot=bot, steps=self.steps)


engine = Engine(  # use Cisco Spark and setup the environment
    type='spark',
    context=context,
    configure=True,
    commands=['shellbot.commands.step', 'shellbot.commands.close'],
    machine_factory=MyFactory(steps=context.get('process.steps')),
    ears=Queue(),)


server = Server(context=context, check=True)  # set web front-end

server.add_route(Notifier(queue=engine.ears,
                          notification={'type': 'event', 'trigger': 'click'},
                          route=context.get('server.trigger')))

server.add_route(Wrapper(callable=engine.get_hook(),
                         route=context.get('server.hook')))


class Handler(object):  # receive web triggers as events from the listener

    def __init__(self, engine):
        self.engine = engine

    def on_inbound(self, received):

        if received.trigger == 'click':
            counter = self.engine.context.increment('pushy.counter')
            logging.info(u'Trigger {}'.format(counter))

            if counter == 1:
                self.bot = self.engine.get_bot()

            else:
                self.bot.say(u'Click {}'.format(counter))


handler = Handler(engine)
engine.register('inbound', handler)

print(u"Trigger this web server from a browser at /trigger")
engine.run(server=server)  # until Ctl-C
