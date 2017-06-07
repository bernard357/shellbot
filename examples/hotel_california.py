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
Hotel California

In this example we show how to keep people in the same room. Following command
is used:

- command: hotel open
- response: **Hotel California** mode activated!

- command: hotel close
- response: **Hotel California** mode deactivated!

- command: hotem
- provides current status of the hotel: open or close

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
    python hotel_california.py


Credit: https://github.com/flint-bot/flint
"""

import os
import time

from shellbot import ShellBot, Context, Command
Context.set_logger()

#
# create a bot and load commands
#


class Open(Command):
    keyword = 'open'
    information_message = u"Open Hotel California"

    def execute(self, arguments=None):
        if self.bot.get('hotel_california.state', 'off') == 'on':
            self.bot.say('Hotel California mode is already activated!')
        else:
            self.bot.set('hotel_california.state', 'on')
            self.bot.say('Hotel California mode activated!')


class Close(Command):
    keyword = 'close'
    information_message = u"Close Hotel California"

    def execute(self, arguments=None):
        if self.bot.get('hotel_california.state', 'off') == 'off':
            self.bot.say('Hotel California mode is already deactivated!')
        else:
            self.bot.set('hotel_california.state', 'off')
            self.bot.say('Hotel California mode deactivated!')


bot = ShellBot(commands=[Open(), Close()])

# load configuration
#
os.environ['BOT_ON_START'] = 'On a dark desert highway, cool wind in my hair...'
os.environ['CHAT_ROOM_TITLE'] = 'Hotel California'
bot.configure()

# initialise a chat room
#
bot.bond(reset=True)

# add stickiness to the hotel
#

class Magic(object):

    def __init__(self, bot):
        self.bot = bot
        self.addresses = set()

    def on_join(self, received):

        if received.actor_address not in self.addresses:
            self.addresses.add(received.actor_address)
            self.bot.say(u"Welcome to Hotel California, {}".format(received.actor_label))

    def on_leave(self, received):

        if self.bot.get('hotel_california.state', 'off') == 'off':
            self.addresses.discard(received.actor_address)
            self.bot.say('On a dark desert highway, cool wind in my hair...')

        else:
            self.bot.say('Such a lovely place...')
            time.sleep(5)
            self.bot.add_participant(received.actor_address)
            self.bot.say(
                u'{}, you can check out any time you like, but you can never leave!'.format(received.actor_label),
                content=u'<@personEmail:{}|{}>, you can **check out any time you like**, but you can **never** leave!'.format(received.actor_address, received.actor_label))

magic = Magic(bot=bot)
bot.register('join', magic)
bot.register('leave', magic)

# run the bot
#
bot.run()

# delete the chat room when the bot is stopped
#
bot.dispose()
