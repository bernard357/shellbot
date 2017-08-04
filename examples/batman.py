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
Chat with Batman

In this example we create following commands with some lines of code:

- command: whoareyou
- response: I'm Batman!

- command: cave
- response: The Batcave is silent...

- command: cave give me some echo
- response: The Batcave echoes, 'give me some echo'

- command: signal
- response: NANA NANA NANA NANA
- also uploads an image to the chat channel

- command: suicide
- delayed response: Going back to Hell
- also deletes the group channel where the command was executed


Multiple questions are adressed in this example:

- How to build a dynamic response? Look at the command ``cave``, where
  the message pushed to the chat channel depends on the input received. This
  is done with regular python code in the member function ``execute()``.

- How to upload files? The command ``signal`` demonstrates how to
  attach a link or a file to a message. Here we use public image, yet the
  same would work for the upload of a local file.

- How to load multiple commands? Since each command is a separate object,
  you can add them as a list bundle to the bot.

- What about commands that do not apply to direct channels? In that case, you
  can set the command attribute ``in_direct`` to False. In this example, the bot
  is not entitled to delete a private channel. So we disable the command
  ``suicide`` from direct channels. If you use the command ``help`` both in
  group channel and in direct channel, you will see that the list is different.


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
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python batman.py


Credit: https://developer.ciscospark.com/blog/blog-details-8110.html
"""

import os
import time

from shellbot import Engine, Context, Command
Context.set_logger()


class Batman(Command):  # a command that displays static text
    keyword = 'whoareyou'
    information_message = u"I'm Batman!"


class Batcave(Command):  # a command that reflects input from the end user
    keyword = 'cave'
    information_message = u"The Batcave is silent..."

    def execute(self, bot, arguments=None, **kwargs):
        if arguments:
            bot.say(u"The Batcave echoes, '{0}'".format(arguments))
        else:
            bot.say(self.information_message)


class Batsignal(Command):  # a command that uploads a file/link
    keyword = 'signal'
    information_message = u"NANA NANA NANA NANA"
    information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

    def execute(self, bot, arguments=None, **kwargs):
        bot.say(self.information_message,
                file=self.information_file)


class Batsuicide(Command):  # a command only for group channels
    keyword = 'suicide'
    information_message = u"Go back to Hell"
    in_direct = False

    def execute(self, bot, arguments=None, **kwargs):
        bot.say(self.information_message)
        bot.dispose()


engine = Engine(  # use Cisco Spark and load shell commands
    type='spark',
    commands=[Batman(), Batcave(), Batsignal(), Batsuicide()])

os.environ['BOT_ON_ENTER'] = 'You can now chat with Batman'
os.environ['BOT_ON_EXIT'] = 'Batman is now quitting the room, bye'
os.environ['CHAT_ROOM_TITLE'] = 'Chat with Batman'
engine.configure()  # ensure that all components are ready

engine.bond(reset=True)  # create a group channel for this example
engine.run()  # until Ctl-C
engine.dispose()  # delete the initial group channel
