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


Here we showcase how a bot manages information over time. A simple
todo list is added to a room, and any participant is entitled to act on it.

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
    python todos.py


"""

import os

from shellbot import ShellBot, Context
Context.set_logger()

#
# create a bot and load commands
#

from todos import TodoFactory
factory = TodoFactory([
    'write down the driving question',
    'gather facts and related information',
    'identify information gaps and document assumptions',
    'formulate scenarios',
    'select the most appropriate scenario',
])

bot = ShellBot(commands=TodoFactory.commands())
bot.factory = factory

# load configuration
#
os.environ['BOT_ON_START'] = 'What do you want to do today?'
os.environ['BOT_ON_STOP'] = 'Bot is now quitting the room, bye'
os.environ['CHAT_ROOM_TITLE'] = 'Manage todos'
bot.configure()

# initialise a chat room
#
bot.bond(reset=True)

# run the bot
#
bot.run()

# delete the chat room when the bot is stopped
#
bot.space.dispose()
