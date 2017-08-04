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
- provides clear status if this channel is currently audited or not

- command: audit on
- starts auditing

- command: audit off
- ensure private interactions for some time


Multiple questions are adressed in this example:

- How to audit chat channels? There are mechanisms built in shellbot by which
  you can received updates from the chat space and forward these to a safe
  place. For this you will need: an audit token that can receive updates,
  a shell command for starting and stopping the audit, and a component to
  handle updates, namely, an updater. All these are featured below.

- What can be done with audited updates? The module ``shellbot.updaters``
  offers standard solutions: write to log files, index updates in ELK, or events
  reflect updates in a sister channel. We expect that more updaters will be
  developed over time by the community. And of course, you can built your own.

- How to customize the handling of audited updates? Shellbot just invoke the
  member function ``put()`` from every updater. There are really no other
  constraints. Shellbot creates one updater instance per bot that it manages.
  This is delegated to the updater factory that is provided on engine
  initialisation.


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
    python audit.py

"""

import logging
from multiprocessing import Process, Queue
import os

from shellbot import Engine, Context
from shellbot.updaters import FileUpdater
Context.set_logger()


class UpdaterFactory(object):  # create one updater per group channel
    def get_updater(self, id):
        return FileUpdater(path='./updater-{}.log'.format(id))


engine = Engine(  # use Cisco Spark and setup audit environment
    type='spark',
    command='shellbot.commands.audit',
    updater_factory=UpdaterFactory())

os.environ['CHAT_ROOM_TITLE'] = 'Audit tutorial'
engine.configure()  # ensure all components are ready

engine.bond(reset=True)  # create a group channel for this example
engine.run()  # until Ctl-C
engine.dispose()  # delete the initial group channel
