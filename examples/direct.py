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
Direct interaction

In this example we start an interaction in a direct channel and then
create a group channel to follow-up.

To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python direct.py


"""

import logging
from multiprocessing import Process
import os
import time

from shellbot import Engine, Context
from shellbot.machines import Input
Context.set_logger()

#
#
#

class MyInput(Input):

    def on_stop(self):

        self.bot.say(u"Switching to a group channel")

        logging.debug(u"- setting lock")
        self.bot.engine.set('general.lock', 'on')

        # create a group channel from the API
        title = 'Now in a group'
        logging.debug(u"- creating channel '{}''".format(title))
        channel = self.bot.space.create(title=title)

        # push content to the store of the new channel
        logging.debug(u"- pushing initial data for bot store")
        label = "store.{}".format(channel.id)
        self.bot.engine.set(
            label,
            {'from': self.bot.id,
             'input': self.bot.recall('input')},
        )

        logging.debug(u"- {}: {}".format(label, self.bot.engine.get(label)))

        # add participants
        participants = self.bot.space.get('participants', [])
        self.bot.space.add_participants(id=channel.id, persons=participants)

        logging.debug(u"- releasing lock")
        self.bot.engine.set('general.lock', 'off')

        # ask the listener to load and start the related bot
#        self.bot.engine.ears.put({'type': 'load_bot', 'id': channel.id})


class MyMachineFactory(object):

    def get_machine(self, bot):

        if bot.channel.is_direct:
            return MyInput(bot=bot,
                         question="PO number please?",
                         mask="9999A",
                         on_retry="PO number should have 4 digits and a letter",
                         on_answer="Ok, PO number has been noted: {}",
                         on_cancel="Ok, forget about the PO number",
                         key='order.id')

#
# create a bot and configure it
#
engine = Engine(type='spark',
                command='shellbot.commands.input',
                machine_factory=MyMachineFactory())
os.environ['CHAT_ROOM_TITLE'] = '*dummy'
engine.configure()

# add some event handler
#
class Handler(object):

    def __init__(self, engine):
        self.engine = engine

    def on_enter(self, received):

        while self.engine.get('general.lock', 'off') == 'on':
            time.sleep(0.001)

#        print("ENTER: {}".format(received))
        bot = self.engine.get_bot(received.channel_id)

        if bot.channel.is_direct:
            bot.say("Please give me your attention please")

        else:
            bot.say(u"Happy to enter '{}'".format(bot.title))

    def on_exit(self, received):
#        print("EXIT: {}".format(received))
        logging.info(u"Sad to exit")

    def on_join(self, received):

        while self.engine.get('general.lock', 'off') == 'on':
            time.sleep(0.001)

#        print("JOIN: {}".format(received))
        bot = self.engine.get_bot(received.channel_id)

        bot.say(u"Welcome to '{}' in '{}'".format(
            received.actor_label, bot.title))

    def on_leave(self, received):
#        print("LEAVE: {}".format(received))
        bot = self.engine.get_bot(received.channel_id)
        bot.say(u"Bye bye '{}', we will miss you in '{}'".format(
            received.actor_label, bot.title))


handler = Handler(engine)
engine.register('enter', handler)
engine.register('exit', handler)
engine.register('join', handler)
engine.register('leave', handler)

#
# run the server
#
engine.run()
