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
The downgraded Hello, World!

In this example we create a shell with one simple command: hello.
Moreover, an automated interaction is ran, and there is no need for internet
access to see the outcome.

Multiple questions are adressed in this example:

- How to avoid chat in the cloud? By selecting a bot with type ``local``, we
  load a minimum textual interface instead of relying on a heavy cloud service.
  Developers will enjoy the capability that is given here to test
  new code interactively, including commands, state machines, or data stores.
  Configuration needs are reduced to the very minimum, and you can stay in a
  terminal window for a larger part of your developments. This is also very
  useful when you do not have access to the internet.

- How to simulate a chat locally? You can inject lines that would be typed
  by a chat participant in the parameter ``input`` of the new bot. When you
  do this, the bot processes all lines one by one, and displays computed
  responses as well. With this approach you can develop and test sophisticated
  interactions, and reproduce them at will.


For example, if you run this script under Linux or macOs::

    python hello_simulator.py


"""

import logging
import os

from shellbot import ShellBot, Context, Command
from shellbot.spaces import SpaceFactory
Context.set_logger(level=logging.INFO)

# create a local bot and load command
#
class Hello(Command):
    keyword = 'hello'
    information_message = u"Hello, World!"

bot = ShellBot(command=Hello(), type='local')

# simulate the execution of commands
#
bot.space.push(['help', 'hello', 'help help'])

bot.configure()
bot.bond()
bot.run()
