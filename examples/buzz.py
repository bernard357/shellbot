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
Fly with Buzz

In this example we cover the situation where commands take significant
time to execute. How to deal with long-lasting transactions?

Also, this example support following commands:

- command: planets
- list available destinations

- command: explore <planet>
- you then track in real-time the progress of the mission

- command: blast <planet>
- similar to exploration, except that the planet is nuked


Multiple questions are adressed in this example:

- How to handle long-lasting transactions? Commands should be written with
  responsiveness in mind. If some heavy processing is considered, this should
  be implemented in a separate object. The shell command would only trigger it,
  but not run it. Below we explain how we implement long flights in space with
  shellbot, so keep reading!

- How to store data for each bot? In this example, the list of available
  planets evolve over time, depending of which planets the end user decides to
  nuke. So, if Mercury is blasted in one channel, and Mercury in another
  channel, there is a need for independant management of planets. In the code
  below you learn how to use ``bot.remember()`` and ``bot.recall()`` and
  manage bot-specific data.

- How to run a standalone process for each bot? As featured below, pass
  a custom driver to the engine that will be used for the creation of each bot.
  The driver can add attributes (here, a rocket) and start processes as well.


Buzz is flying from Earth to some planets and come back. Obviously,
this is the kind of activity that can take ages, yet here each mission
lasts about 30 seconds.

Ok. So, when I type ``explore Uranus`` in the chat box, do I have to
wait for 30 seconds before the next command is considered? Hopefully not!

The two commands ``explore`` and ``blast`` are non-interactive. This means
that they are pushed to a pipeline for background execution.

With this concept, you can get a dialog similar to the following::

    > buzz explore Mercury

    Ok, I am working on it
    #1 - Departing to Mercury

    > buzz blast Neptune

    Ok, will work on it as soon as possible
    #1 - Approaching Mercury
    #1 - Landed on Mercury

    > buzz planets

    Available destinations:
    - Venus
    - Moon

    ...

In other terms, the bot is always responsive, whatever is executing in the
background. Also, non-interactive commands are executed in the exact
sequence of their submission.

These concepts are implemented with instances of ``Rocket`` that are
attached to bots. Every rocket has a queue that receives commands submitted
in the chat box. And of course, every rocket is runnning a separate process
to pick up new missions and to execute them.

To run this script you have to provide a custom configuration, or set
environment variables instead:

- ``CHANNEL_DEFAULT_PARTICIPANTS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHANNEL_DEFAULT_PARTICIPANTS="alice@acme.com"
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python buzz.py

"""

import os

from shellbot import Engine, ShellBot, Context
from planets import PlanetFactory
from planets.rocket import Rocket
Context.set_logger()


class FlyingBot(ShellBot):  # add a rocket to each bot
    def on_init(self):
        self.rocket = Rocket(self)
        self.rocket.start()


engine = Engine(type='spark',  # use Cisco Spark and setup flying envronment
                commands=PlanetFactory.commands(),
                driver=FlyingBot)

os.environ['BOT_ON_ENTER'] = 'Hello Buzz, welcome to Cape Canaveral'
os.environ['BOT_ON_EXIT'] = 'Batman is now quitting the room, bye'
os.environ['CHAT_ROOM_TITLE'] = 'Buzz flights'
engine.configure()  # ensure that all components are ready

engine.set('bot.store.planets', ['Mercury',
                                 'Venus',
                                 'Moon',
                                 'Mars',
                                 'Jupiter',
                                 'Saturn',
                                 'Uranus',
                                 'Neptune',
                                 ])

engine.bond(reset=True)  # create a group channel for this example
engine.run()  # until Ctl-C
engine.dispose()  # delete the initial group channel
