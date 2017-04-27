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
- response: Going back to Hell
- also stops the bot itself on the server

To run this script you have to change the configuration below, or set
environment variables instead.

Put the token received from Cisco Spark for your bot in
a variable named ``SHELLY_TOKEN``::

    export SHELLY_TOKEN="<token id from Cisco Spark for Developers>"

The variable ``SERVER_URL`` has to mention the public IP address and link
used to reach this server from the Internet. For example, if you use ngrok
during development and test::

    export SERVER_URL="http://1a107f21.ngrok.io"


Credit: https://developer.ciscospark.com/blog/blog-details-8110.html
"""

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

#
# load configuration
#

bot.configure({

    'bot': {
        'on_start': 'You can now chat with Batman',
        'on_stop': 'Batman is now quitting the room, bye',
    },

    'spark': {
        'room': 'Chat with Batman',
        'moderators': 'bernard.paques@dimensiondata.com',
        'token': '$SHELLY_TOKEN',
    },

    'server': {
        'url': '$SERVER_URL',
        'hook': '/hook',
        'binding': '0.0.0.0',
        'port': 8080,
    },

})

#
# initialise a chat room
#

bot.bond(reset=True)

#
# run the bot
#

bot.run()

#
# delete the chat room
#

bot.dispose()
