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
Hello, World!

In this example we create a shell with one simple command: hello

Multiple questions are adressed in this example:

- How to change the banner? Shellbot support bare text, rich content, and even
  some upload, all together. This can be changed by adjusting some environment
  variables, as shown below.

- How to build a basic command that displays a message? Look at the
  command ``hello`` below, this is really done in some lines of code.

- How to provide with rich content? Here we use Markdown so that input
  provided by the end user is smartly reflected by the bot.

- How to react to file upload? In shellbot, commands receive everything
  that is flowing from the underlying chat space, including file uploads.

- How to use Cisco Spark? As shown below, the platform is selected during
  the initialisation of the engine. Here we put ``type='spark'`` and that's it.
  Ok, in addition to this code you also have to set some variables to make it
  work, but this is regular configuration, done outside the code itself.


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
    python hello.py

"""

import os

from shellbot import Engine, Context, Command
Context.set_logger()


class Hello(Command):  # the origin of everything, right?
    keyword = 'hello'
    information_message = u"Hello, World!"

    feedback_content = u"Hello, **{}**!"
    thanks_content = u"Thanks for the upload of `{}`"

    def execute(self, bot, arguments=None, attachment=None, url=None, **kwargs):

        bot.say(content=self.feedback_content.format(
            arguments if arguments else 'World'))

        if attachment:
            bot.say(content=self.thanks_content.format(attachment))


engine = Engine(type='spark', command=Hello())

os.environ['CHAT_ROOM_TITLE'] = 'Hello tutorial'
os.environ['BOT_BANNER_TEXT'] = u"Type '@{} help' for more information"
os.environ['BOT_BANNER_CONTENT'] = (u"Hello there! "
                                    u"Type ``@{} help`` at any time and  get "
                                    u"more information on available commands.")
os.environ['BOT_BANNER_FILE'] = \
    "http://skinali.com.ua/img/gallery/19/thumbs/thumb_m_s_7369.jpg"

engine.configure()  # ensure that all components are ready

engine.bond(reset=True)  # create a group channel for this example
engine.run()  # until Ctl-C
engine.dispose()  # delete the initial group channel
