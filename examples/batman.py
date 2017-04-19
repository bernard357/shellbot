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

Credit: https://developer.ciscospark.com/blog/blog-details-8110.html
"""

import logging
import os
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import ShellBot, Context, Command, Server, Wrapper
Context.set_logger()

#
# load configuration
#

settings = {

    'bot': {
        'on_start': 'You can now chat with Batman',
        'on_stop': 'Batman is now quitting the room, bye',
    },

    'spark': {
        'room': 'Chat with Batman',
        'moderators': 'bernard.paques@dimensiondata.com',
    },

    'server': {
        'url': 'http://5ad34e5b.ngrok.io',
        'hook': '/hook',
        'binding': '0.0.0.0',
        'port': 8080,
    },

}

context = Context(settings)

#
# create a bot and load commands
#

bot = ShellBot(context=context, check=True)


class Batman(Command):
    keyword = 'whoareyou'
    information_message = "I'm Batman!"


class Batcave(Command):
    keyword = 'cave'
    information_message = "The Batcave is silent..."

    def execute(self, arguments=None):
        if arguments:
            self.bot.say("The Batcave echoes, '{0}'".format(arguments))
        else:
            self.bot.say(self.information_message)


class Batsignal(Command):
    keyword = 'signal'
    information_message = "NANA NANA NANA NANA"
    information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

    def execute(self, arguments=None):
        self.bot.say(self.information_message,
                     file=self.information_file)


class Batsuicide(Command):
    keyword = 'suicide'
    information_message = "Going back to Hell"
    is_interactive = False

    def execute(self, arguments=None):
        time.sleep(3)
        self.bot.say(self.information_message)
        self.bot.stop()


bot.load_commands([Batman(), Batcave(), Batsignal(), Batsuicide()])

#
# initialise a suitable chat room
#

bot.bond(reset=True)

#
# run the bot
#

server = None

if context.get('server.binding') is not None:
    server = Server(context=context, check=True)
    bot.hook(server=server)

bot.run(server=server)

bot.space.dispose(bot.context.get('spark.room'))
