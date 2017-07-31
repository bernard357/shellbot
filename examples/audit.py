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
Audit interactions in real-time

In this example we create a shell with one simple command: audit

- command: audit
- provides clear status if this room is currently audited or not

- command: audit on
- starts auditing

- command: audit off
- ensure private interactions for some time


To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHANNEL_DEFAULT_PARTICIPANTS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``CISCO_SPARK_AUDIT_TOKEN`` - The Cisco Spark token used for audit
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The bot token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

The other token should be associated to a human being, and not to a bot.
This is required so that the software can receive all events for a chat space.
Without it, only messages sent to the bot will be audited.

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHANNEL_DEFAULT_PARTICIPANTS="alice@acme.com"
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for bot>"
    export CISCO_SPARK_AUDIT_TOKEN="<token id from Cisco Spark for audit>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python hello.py


"""

import logging
from multiprocessing import Process, Queue
import os

from shellbot import Engine, Context, Command, Speaker
from shellbot.commands import Audit
from shellbot.spaces import SparkSpace
from shellbot.updaters import FileUpdater
Context.set_logger()


# for chat audit, create one updater per channel
#
class UpdaterFactory(object):
    def get_updater(self, id):
        return FileUpdater(path='./updater-{}.log'.format(id))

# create a chat engine
#
engine = Engine(
    type='spark',
    command='shellbot.commands.audit',
    updater_factory=UpdaterFactory())

# load configuration
#
os.environ['CHAT_ROOM_TITLE'] = 'Audit tutorial'
engine.configure()

# create a chat room
#
engine.bond(reset=True)

# run the bot
#
engine.run()

# delete the chat room when the bot is stopped
#
engine.dispose()
