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

from bottle import request
import logging
from multiprocessing import Process, Queue
import os
from six import string_types
import sys
import time

from shellbot.events import Message
from .base import Space


class LocalSpace(Space):
    """
    Handles chat locally

    This class allows developers to test their commands interface
    locally, without the need for a real API back-end.

    Example::

        bot = ShellBot(command=Hello(), type='local')
        bot.space.push(['help', 'hello', 'help help'])

        bot.configure()
        bot.bond()
        bot.run()

    """

    DEFAULT_PROMPT = u'> '

    def on_init(self, prefix='local', input=None, **kwargs):
        """
        Adds processing to space initialisation

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        :param input: Lines of text to be submitted to the chat
        :type input: str or list of str

        Example::

            space = LocalSpace(bot=bot, prefix='local.audit')

        Here we create a new local space, and use
        settings under the key ``local.audit`` in the context of this bot.

        Example::

            space = LocalSpace(bot=bot, input='hello world')

        Here we create a new local space, and simulate a user
        typing 'hello world' in the chat space.

        """
        assert prefix not in (None, '')
        self.prefix = prefix

        self.input = []
        self.push(input)

        self.prompt = self.DEFAULT_PROMPT

        self.moderators = []
        self.participants = []

    def push(self, input):
        """
        Adds more input to this space

        :parameter input: Simulated user input
        :type input: str or list of str

        This function is used to simulate input user to the bot.
        """
        if input in (None, ''):
            return
        if isinstance(input, string_types):
            input = [input]
        self.input += input

    def on_reset(self):
        """
        Selects the right input for this local space

        If this space got some content on its initialisation, this is used
        to simulate user input. Else stdin is read one line at a time.
        """
        if self.input:

            def read_list():
                for line in self.input:
                    sys.stdout.write(line+'\n')
                    sys.stdout.flush()
                    yield line

            self._lines = read_list()  #  yield creates an iterator

        else:

            def read_stdin():
                readline = sys.stdin.readline()
                while readline:
                    yield readline.rstrip('\n')
                    readline = sys.stdin.readline()

            self._lines = read_stdin()  #  yield creates an iterator

    def check(self):
        """
        Checks that valid settings are available
        """
        self.bot.context.check(self.prefix+'.title', 'Local space')
        self.bot.context.check(self.prefix+'.moderators', [])
        self.bot.context.check(self.prefix+'.participants', [])

        self.bot.context.set('server.binding', None)  # no web server at all

    def on_bond(self):
        """
        Adds processing to space bond
        """
        self.bot.context.set('bot.id', '*bot')

    def lookup_space(self, title, **kwargs):
        """
        Looks for an existing space by name

        :param title: title of the target space
        :type title: str

        :return: True on successful lookup, False otherwise

        """
        assert title not in (None, '')

        self.id = '*id'
        self.title = title

        return True

    def create_space(self, title, **kwargs):
        """
        Creates a space

        :param title: title of the target space
        :type title: str

        On successful space creation, this object is configured
        to use it.

        """
        assert title not in (None, '')

        self.id = '*id'
        self.title = title

    def add_moderator(self, person):
        """
        Adds one moderator

        :param person: e-mail address of the person to add
        :type person: str

        """
        self.moderators.append(person)

    def add_participant(self, person):
        """
        Adds one participant

        :param person: e-mail address of the person to add
        :type person: str

        """
        self.participants.append(person)

    def delete_space(self, title, **kwargs):
        """
        Deletes a space

        :param title: title of the space to be deleted
        :type title: str

        >>>space.delete_space("Obsolete Space")

        """
        pass
    def post_message(self,
                     text=None,
                     content=None,
                     file=None,
                     **kwargs):
        """
        Posts a message

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as MArkdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        Example message out of plain text::

        >>>space.post_message(text='hello world')

        """
        if content:
            logging.debug(u"- rich content is not supported")

        if file:
            logging.debug(u"- file attachment is not supported")

        sys.stdout.write(text+'\n')
        sys.stdout.flush()

    def on_run(self):
        """
        Adds processing to space beginning of run
        """
        sys.stdout.write(u"Type 'help' for guidance, or Ctl-C to exit.\n")
        sys.stdout.flush()

    def pull(self):
        """
        Fetches updates

        This function senses most recent items, and pushes them
        to the listening queue.

        """
        sys.stdout.write(self.prompt)
        sys.stdout.flush()

        try:
            line = next(self._lines)
            self.on_message({'text': line}, self.bot.ears)
        except StopIteration:
            sys.stdout.write(u'^C\n')
            sys.stdout.flush()
            self.bot.context.set('general.switch', 'off')

    def on_message(self, item, queue):
        """
        Normalizes message for the listener

        :param item: attributes of the inbound message
        :type item: dict

        :param queue: the processing queue
        :type queue: Queue

        This function prepares a Message and push it to the provided queue.

        """
        message = Message(item)
        message.from_id = '*user'
        message.mentioned_ids = ['*bot']

        queue.put(str(message))
