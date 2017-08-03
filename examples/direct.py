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
from shellbot.commands import Command
from shellbot.machines import MachineFactory, Input
Context.set_logger()


# on data capture in direct channel, create and initialise a group channel
#
class MyInput(Input):

    def on_stop(self):

        self.bot.say(u"Switching to a group channel:")

        logging.debug(u"- prevent racing conditions from webhooks")
        self.bot.engine.set('listener.lock', 'on')

        title = 'Follow-up in group room #{}'.format(
            self.bot.store.increment('group.count'))
        self.bot.say(u"- creating channel '{}'...".format(title))
        team_title = 'shellbot environment'
        channel = self.bot.space.create(title=title,
                                        ex_team=team_title)

        self.bot.say(u"- pushing input data to the group channel...")
        label = "store.{}".format(channel.id)
        self.bot.engine.set(
            label,
            {'from': self.bot.id,
             'input': self.bot.recall('input')},
        )

        self.bot.say(u"- replicating documents to the group channel...")
        counter = 0
        for message in self.bot.space.list_messages(id=self.bot.id,
                                                    quantity=1,
                                                    with_attachment=True):
            if not counter:
                self.bot.space.post_message(channel.id,
                                            text="Documents gathered so far:")
            counter += 1
            self.bot.say(u"- replicating document #{}...".format(counter))

            name = self.bot.space.name_attachment(message.url)
            logging.debug(u"- attachment: {}".format(name))
            downloaded = self.bot.space.download_attachment(message.url)
            self.bot.space.post_message(id=channel.id,
                                        text=name,
                                        file=downloaded)

        self.bot.say(u"- adding participants to the group channel...")
        participants = self.bot.space.list_participants(self.bot.id)

        for person in self.bot.space.get('participants', []):
            participants.add(person)

        self.bot.space.add_participants(id=channel.id, persons=participants)

        self.bot.space.post_message(channel.id,
                                    content="Use command ``input`` to view data gathered so far.")

        logging.debug(u"- releasing listener lock")
        self.bot.engine.set('listener.lock', 'off')

        self.bot.say(u"- done")
        self.bot.say(content=u"Please go to the new channel for group interactions. Come back here and type ``start`` for a new sequence.")


# we use state machines only in direct channels
#
class MyMachineFactory(MachineFactory):

    def get_machine_for_direct_channel(self, bot):

        return MyInput(bot=bot,
                       question="PO number please?",
                       mask="9999A",
                       on_retry="PO number should have 4 digits and a letter",
                       on_answer="Ok, PO number has been noted: {}",
                       on_cancel="Ok, forget about the PO number",
                       key='order.id')

    def get_machine_for_group_channel(self, bot):
        return None

    def get_default_machine(self, bot):
        return None


# create a bot and configure it
#
engine = Engine(type='spark',
                commands=['shellbot.commands.input',
                          'shellbot.commands.start',
                          'shellbot.commands.close',
                          ],
                machine_factory=MyMachineFactory())

os.environ['CHAT_ROOM_TITLE'] = '*dummy'
engine.configure()

# run the engine
#
print(u"Go to Cisco Spark and engage with the bot in a direct channel")
engine.run()
