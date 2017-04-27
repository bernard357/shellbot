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
Manage todos

In this example we create following commands with some lines of code:

- command: todo <something to do>
- show the # of the new item in response

- command: todo #<n> <something to do>
- show the updated item in response

- command: todos
- list all thing to do

- command: next
- show next item to do

- command: done
- signal that one item has been completed

- command: history
- lists completed items

- command: drop
- command: drop #<n>
- to delete one item

To run this script you have to change the configuration below, or set
environment variables instead.

Put the token received from Cisco Spark for your bot in
a variable named ``SHELLY_TOKEN``::

    export SHELLY_TOKEN="<token id from Cisco Spark for Developers>"

The variable ``SERVER_URL`` has to mention the public IP address and link
used to reach this server from the Internet. For example, if you use ngrok
during development and test::

    export SERVER_URL="http://1a107f21.ngrok.io"

"""

import logging
from multiprocessing import Process, Queue
import os
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import ShellBot, Context, Command, Server
Context.set_logger()

#
# load configuration
#

settings = {

    'bot': {
        'on_start': 'You can manage items to do',
        'on_stop': 'Bot is now quitting the room, bye',
    },

    'todos.items': [
        'write down the driving question',
        'gather facts and related information',
        'identify information gaps and document assumptions',
        'formulate scenarios',
        'select the most appropriate scenario',
    ],

    'spark': {
        'room': 'Manage Todos',
        'moderators': 'bernard.paques@dimensiondata.com',
        'token': '$SHELLY_TOKEN',
    },

    'server': {
        'url': '$SERVER_URL',
        'hook': '/hook',
        'binding': '0.0.0.0',
        'port': 8080,
    },

}

context = Context(settings)

#
# create a bot and load commands
#

bot = ShellBot(context=context,
               configure=True,
               ears=Queue(),
               inbox=Queue(),
               mouth=Queue())

from todos import TodoFactory
bot.factory = TodoFactory(bot.context.get('todos.items', []))
bot.load_commands(TodoFactory.commands())

#
# initialise a suitable chat room
#

bot.bond(reset=True)

#
# run the bot
#

server = None

if context.get('server.binding') is not None:
    server = Server(context=context, check=True)
    bot.hook(server=server)

bot.run(server=server)

bot.space.dispose()
