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

- command: open
- response: **Hotel California** mode activated!

- command: close
- response: **Hotel California** mode deactivated!

- command: hotel
- provides current status of the hotel: open or close

To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHANNEL_DEFAULT_PARTICIPANTS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``CISCO_SPARK_TOKEN`` - Your personal Cisco Spark token
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

The other token should be associated to a human being, and not to a bot.
This is required so that the software can receive all events for a chat space.
Without it, the bot may not see who is leaving or joining.

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHANNEL_DEFAULT_PARTICIPANTS="alice@acme.com"
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export CISCO_SPARK_TOKEN="<personal token id from Cisco Spark>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python hotel_california.py


Credit: https://github.com/flint-bot/flint
"""

import os
import time

from shellbot import Engine, ShellBot, Context, Command
Context.set_logger()

#
# create a bot and load commands
#


class Open(Command):
    keyword = 'open'
    information_message = u"Open Hotel California"

    def execute(self, bot, arguments=None, **kwargs):
        if bot.channel.is_direct:
            bot.say('This is a private place, not an hotel')
        elif bot.recall('hotel_california.state', 'off') == 'on':
            bot.say('Hotel California mode is already activated!')
        else:
            bot.remember('hotel_california.state', 'on')
            bot.say('Hotel California mode activated!')


class Close(Command):
    keyword = 'close'
    information_message = u"Close Hotel California"

    def execute(self, bot, arguments=None, **kwargs):
        if bot.channel.is_direct:
            bot.say('This is a private place, not an hotel')
        elif bot.recall('hotel_california.state', 'off') == 'off':
            bot.say('Hotel California mode is already deactivated!')
        else:
            bot.remember('hotel_california.state', 'off')
            bot.say('Hotel California mode deactivated!')


class Hotel(Command):
    keyword = 'hotel'
    information_message = u"Get status of Hotel California"

    def execute(self, bot, arguments=None, **kwargs):
        if bot.channel.is_direct:
            bot.say('This is a private place, not an hotel')
        elif bot.recall('hotel_california.state', 'off') == 'off':
            bot.say('Hotel California will let you escape')
        else:
            bot.say('Hotel California will keep you here forever!')


engine = Engine(type='spark', commands=[Open(), Close(), Hotel()])

# load configuration
#
os.environ['BOT_ON_ENTER'] = 'On a dark desert highway, cool wind in my hair...'
os.environ['CHAT_ROOM_TITLE'] = 'Hotel California'
engine.configure()

# add stickiness to the hotel
#

class Magic(object):

    def __init__(self, engine):
        self.engine = engine

    def on_join(self, received):  # called from listenr process

        bot = self.engine.get_bot(received.channel_id)
        addresses = bot.recall('visitors', [])

        if received.actor_address not in addresses:
            addresses.append(received.actor_address)
            bot.remember('visitors', addresses)
            bot.say(u"Welcome to Hotel California, {}".format(received.actor_label))

    def on_leave(self, received):  # called from listener process

        bot = self.engine.get_bot(received.channel_id)
        addresses = bot.recall('visitors', [])

        if bot.recall('hotel_california.state', 'off') == 'off':
            try:
                addresses.remove(received.actor_address)
            except ValueError:
                pass
            bot.remember('visitors', addresses)
            bot.say('On a dark desert highway, cool wind in my hair...')

        else:
            bot.say('Such a lovely place...')
            time.sleep(5)
            bot.add_participant(received.actor_address)
            bot.say(
                u'{}, you can check out any time you like, but you can never leave!'.format(received.actor_label),
                content=u'<@personEmail:{}|{}>, you can **check out any time you like**, but you can **never** leave!'.format(received.actor_address, received.actor_label))

magic = Magic(engine=engine)
engine.register('join', magic)
engine.register('leave', magic)

# create a chat room
#
engine.bond(reset=True)

# run the bot
#
engine.run()

# delete the chat room when the bot is stopped
#
engine.dispose()
