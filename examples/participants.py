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
Participants

In this example we show how a bot can be invited into spaces or kicked off.

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
    python participants.py


"""

import logging
from multiprocessing import Process
import os
import time

from shellbot import Engine, Context
from shellbot.machines import Input
Context.set_logger()

#
# specify the state machine to use
#

class MyFactory(object):
    def get_machine(self, bot):
            return Input(bot=bot,
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
                machine_factory=MyFactory())
os.environ['CHAT_ROOM_TITLE'] = '*dummy'
engine.configure()

# add some event handler
#
class Handler(object):

    def __init__(self, engine):
        self.engine = engine

    def on_enter(self, received):
        print("ENTER: {}".format(received))
        bot = self.engine.get_bot(received.channel_id)
        bot.say(u"Happy to enter '{}'".format(bot.title))

    def on_exit(self, received):
        print("EXIT: {}".format(received))
        logging.info(u"Sad to exit")

    def on_join(self, received):
        print("JOIN: {}".format(received))
        bot = self.engine.get_bot(received.channel_id)
        bot.say(u"Welcome to '{}' in '{}'".format(
            received.actor_label, bot.title))

        bot.say(person=received.actor_address, text=u"Please give me your attention please")

        time.sleep(1)
        direct_channel = self.engine.space.get_by_person(received.actor_label)
        if direct_channel:
            direct_bot = self.engine.get_bot(direct_channel.id)
            if direct_bot.machine and not direct_bot.machine.is_running:
                direct_bot.machine.restart()

    def on_leave(self, received):
        print("LEAVE: {}".format(received))
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
