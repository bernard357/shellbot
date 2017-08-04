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
todo list is added to the engine, and any participant is entitled to act on it,
from any channel.

Multiple questions are adressed in this example:

- How to share information across multiple channels? You can attach any
  attribute to the engine, and this will be made available to every bot
  instance. Here we add ``factory`` to the engine, and it is accessed from
  within commands as ``bot.engine.factory``.

To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHANNEL_DEFAULT_PARTICIPANTS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHANNEL_DEFAULT_PARTICIPANTS="alice@acme.com"
    export CHAT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python todos.py


"""

import os

from shellbot import Engine, Context
from todos import TodoFactory
Context.set_logger()

factory = TodoFactory([
    'write down the driving question',
    'gather facts and related information',
    'identify information gaps and document assumptions',
    'formulate scenarios',
    'select the most appropriate scenario',
])

engine = Engine(  # use Cisco Spark and load shell commands
    type='spark', 
    commands=TodoFactory.commands())
engine.factory = factory

os.environ['BOT_ON_ENTER'] = 'What do you want to do today?'
os.environ['CHAT_ROOM_TITLE'] = 'Manage todos'
engine.configure()  # ensure that all components are ready

engine.bond(reset=True)  # create a group channel for this example
engine.run()  # until Ctl-C
engine.dispose()  # delete the initial group channel
