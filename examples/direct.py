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

Following commands are used in this example:

- command: start
- this is used in a direct channel to start a new transaction

- command: input
- reflect data that has been captured so far

- command: close
- this is used in a group channel to destroy it


Multiple questions are adressed in this example:

- How to engage with a bot in a direct channel? When the end user
  invites the bot in a direct channel, a first transaction starts immediately.
  Later on, the command ``start`` is used on each new transaction. In essence,
  this command resets and restarts the underlying state machine, so the design
  is really generic. In this example we use a simple state machine derived
  from ``Input`` for this purpose. For more sophisticated situations, you
  could consider ``Menu``, ``Sequence`` and ``Steps`` as well.
  Or write your own state machine if needed.

- How to ask for data and manage the capture? Shellbot provides with mask and
  with regex expressions to validate information provided by end users. The
  state machines also provide tip and help information, or give up on time-out.

- How to list participants of a channel? Here we retrieve the address of
  end user in direct channel, and add him to the participants of the new group
  channel. Look for ``bot.list_participants()`` in the code below.

- How to store data that has been captured? State machines coming with shellbot
  save captured data in the store attached to each bot. In the example below,
  the state machine is configured to use the key ``order.id``. This is
  done in a specialized list of key-value pairs named ``input``.

- How to display data that has been captured from the end user? Type the command
  ``input`` and that's it.

- How to populate a bot store? When a bot is created, shellbot initializes it
  with content from the context. First, shellbot looks for generic key
  ``bot.store``. Second, shellbot also consider the key ``store.<channel_id>``
  for content that is specific to one bot. Here we use the second mechanism so
  that input captured in a direct channel is replicated to the store of the
  group channel.

- How to retrieve attachments from a channel? This capablity is required to
  replicate a document from the direct channel to the group channel.
  Attachments are listed from ``bot.space.list_message()``, with the addition
  of flag ``with_attachment``. Based on this, attachments can be downloaded
  on local computer, and uploaded as updates of the group channel. Look at the
  code, it is rather self-explanatory.

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
import os
import time

from shellbot import Engine, Context
from shellbot.machines import MachineFactory, Input
Context.set_logger()


class MyInput(Input):  # transition from direct channel to group channel

    def on_stop(self):

        team_title = 'shellbot environment'

        title = 'Follow-up in group room #{}'.format(
            self.bot.store.increment('group.count'))

        self.bot.say(u"Switching to a group channel:")

        logging.debug(u"- prevent racing conditions from webhooks")
        self.bot.engine.set('listener.lock', 'on')

        self.bot.say(u"- creating channel '{}'...".format(title))
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

        self.bot.space.post_message(
            channel.id,
            content="Use command ``input`` to view data gathered so far.")

        logging.debug(u"- releasing listener lock")
        self.bot.engine.set('listener.lock', 'off')

        self.bot.say(u"- done")
        self.bot.say(content=(u"Please go to the new channel for group "
                              u"interactions. Come back here and type "
                              u"``start`` for a new sequence."))


class MyMachineFactory(MachineFactory):  # provide machines to direct channels

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


engine = Engine(type='spark',  # use Cisco Spark and setup the environment
                commands=['shellbot.commands.input',
                          'shellbot.commands.start',
                          'shellbot.commands.close',
                          ],
                machine_factory=MyMachineFactory())

os.environ['CHAT_ROOM_TITLE'] = '*dummy'
engine.configure()  # ensure that all components are ready

print(u"Go to Cisco Spark and engage with the bot in a direct channel")
engine.run()  # until Ctl-C
