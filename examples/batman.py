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
- also uploads an image to the chat room

- command: suicide
- delayed response: Going back to Hell
- also stops the bot itself on the server

Multiple questions are adressed in this example:

- How to build a dynamic response? Look at the command ``cave``, where
  the message pushed to the chat room depends on the input received. This
  is done with regular python code in the member function ``execute()``.

- How to upload files? The command ``signal`` demonstrates how to
  attach a link or a file to a message. Here we use public image, yet the
  same would work for the upload of a local file.

- What about long-lasting commands? In that case, you can set the command
  attribute ``is_interactive`` to False. On command submission, the bot
  will execute it in the background. Look for example at the command
  ``suicide``, where Batman is waiting for some seconds before acting.

- How to load multiple commands? Since each command is a separate object,
  you can add them as a list bundle to the bot.


To run this script you have to provide a custom configuration, or set
environment variables instead::

- ``CHAT_ROOM_MODERATORS`` - You have at least your e-mail address
- ``CHAT_TOKEN`` - Received from Cisco Spark when you register your bot
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHAT_ROOM_MODERATORS="alice@acme.com"
    export CHAT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python batman.py


Credit: https://developer.ciscospark.com/blog/blog-details-8110.html
"""

import os
import time

from shellbot import ShellBot, Context, Command
Context.set_logger()

#
# create a bot and load commands
#


class Batman(Command):
    keyword = 'whoareyou'
    information_message = u"I'm Batman!"


class Batcave(Command):
    keyword = 'cave'
    information_message = u"The Batcave is silent..."

    def execute(self, arguments=None):
        if arguments:
            self.bot.say(u"The Batcave echoes, '{0}'".format(arguments))
        else:
            self.bot.say(self.information_message)


class Batsignal(Command):
    keyword = 'signal'
    information_message = u"NANA NANA NANA NANA"
    information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

    def execute(self, arguments=None):
        self.bot.say(self.information_message,
                     file=self.information_file)


class Batsuicide(Command):
    keyword = 'suicide'
    information_message = u"Go back to Hell"
    is_interactive = False

    def execute(self, arguments=None):
        time.sleep(3)
        self.bot.say(self.information_message)
        self.bot.stop()


bot = ShellBot(commands=[Batman(), Batcave(), Batsignal(), Batsuicide()])

# load configuration
#
os.environ['BOT_ON_START'] = 'You can now chat with Batman'
os.environ['BOT_ON_STOP'] = 'Batman is now quitting the room, bye'
os.environ['CHAT_ROOM_TITLE'] = 'Chat with Batman'
bot.configure()

# initialise a chat room
#
bot.bond(reset=True)

# run the bot
#
bot.run()

# delete the chat room when the bot is stopped
#
bot.dispose()
