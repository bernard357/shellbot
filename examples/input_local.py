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
Capture information

In this example we create a pro-active system that asks for information.

Multiple questions are adressed in this example:

- How to avoid chat in the cloud? By selecting a bot with type ``local``, we
  load a minimum textual interface instead of relying on a heavy cloud service.
  Developers will enjoy the capability that is given here to test
  new code interactively, including commands, state machines, or data stores.
  Configuration needs are reduced to the very minimum, and you can stay in a
  terminal window for a larger part of your developments. This is also very
  useful when you do not have access to the internet.

- How to manage the interaction? People do not always react as expected
  when they are queried for data input. Here we use a state machine that insist
  when reaction is delayed, when input is not correct, or when the full
  input is cancelled. Change delays and messages below to test it a bit.


For example, if you run this script under Linux or macOs::

    python input_local.py


"""

import logging
import os

from shellbot import ShellBot, Context, Command
from shellbot.spaces import SpaceFactory
from shellbot.machines import Input, Sequence
Context.set_logger()

# create a local bot
#
bot = ShellBot(type='local', command='shellbot.commands.input')
bot.configure()
bot.bond()

# ask some information
#
order_id = Input(bot=bot,
                question="PO number please?",
                mask="9999A",
                on_retry="PO number should have 4 digits and a letter",
                on_answer="Ok, PO number has been noted: {}",
                on_cancel="Ok, forget about the PO number",
                tip=20,
                timeout=40,
                key='order.id')

description = Input(bot=bot,
                question="Issue description please?",
                on_retry="Please enter a one-line description of the issue",
                on_answer="Ok, description noted: {}",
                on_cancel="Ok, forget about the description",
                tip=20,
                timeout=40,
                key='description')

sequence = Sequence(machines=[order_id, description])
sequence.start()

# interact locally
#
bot.run()
