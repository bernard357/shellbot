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
Fly with Buzz

In this example we create following commands with some lines of code:

- command: explore <planet>
- you then track in real-time the progress of the mission

- command: blast <planet>
- similar to exploration, except that the planet is nuked

- command: planets
- list available destinations

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
    python buzz.py


"""

import os

from shellbot import ShellBot, Context
Context.set_logger()

# create a bot and load commands
#
from planets import PlanetFactory
bot = ShellBot(commands=PlanetFactory.commands())

# load configuration
#
os.environ['BOT_ON_START'] = 'Hello Buzz, welcome to Cape Canaveral'
os.environ['BOT_ON_STOP'] = 'Batman is now quitting the room, bye'
os.environ['CHAT_ROOM_TITLE'] = 'Buzz flights'
bot.configure()
bot.context.set('planets.items', ['Mercury',
                                  'Venus',
                                  'Moon',
                                  'Mars',
                                  'Jupiter',
                                  'Saturn',
                                  'Uranus',
                                  'Neptune',
                                 ])

# initialise a chat room
#
bot.bond(reset=True)

# run the bot
#
bot.run()

# delete the chat room when the bot is stopped
#
bot.dispose()
