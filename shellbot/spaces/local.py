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

    If a list of commands is provided as input, then the space will consume
    all of them and then it will stop. All kinds of automated tests and
    scenarios can be build with this approach.

    Example of automated interaction with some commands::

        engine = Engine(command=Hello(), type='local')
        engine.space.push(['help', 'hello', 'help help'])

        engine.configure()
        engine.run()

    If no input is provided, then the space provides a command-line interface
    so that you can play interactively with your bot. This setup is handy
    since it does not require access to a real chat back-end.

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

            space = LocalSpace(context=context, prefix='local.audit')

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
        self.context.check(self.prefix+'.title', 'Local space', filter=True)
        self.context.check(self.prefix+'.moderators', [], filter=True)
        self.context.check(self.prefix+'.participants', [], filter=True)

        self.context.set('server.binding', None)  # no web server at all

    def on_bond(self):
        """
        Adds processing to space bond
        """
        self.context.set('bot.id', '*bot')

    def use_space(self, id, **kwargs):
        """
        Uses an existing space

        :param id: title of the target space
        :type id: str

        :return: True on success, False otherwise

        If a space already exists with this id, this object is
        configured to use it and the function returns True.

        Else the function returns False.

        This function should be
        """
        assert id not in (None, '')

        self.values['id'] = id
        self.values['title'] = self.configured_title()

        return True

    def lookup_space(self, title, **kwargs):
        """
        Looks for an existing space by name

        :param title: title of the target space
        :type title: str

        :return: True on successful lookup, False otherwise

        """
        assert title not in (None, '')

        self.values['id'] = '*local'
        self.values['title'] = title

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

        self.values['id'] = '*local'
        self.values['title'] = title

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

    def remove_participant(self, person):
        """
        Removes one participant

        :param person: e-mail address of the person to remove
        :type person: str

        """
        self.participants.remove(person)

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
                     space_id=None,
                     **kwargs):
        """
        Posts a message

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as MArkdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        :param space_id: unique id of the target space
        :type space_id: str

        Example message out of plain text::

        >>>space.post_message(text='hello world')

        If no space id is provided, then the function can use the unique id
        of this space, if one has been defined. Or an exception may be raised
        if no id has been made available.

        """
        if content:
            logging.debug(u"- rich content is not supported")

        if file:
            logging.debug(u"- file attachment is not supported")

        sys.stdout.write(text+'\n')
        sys.stdout.flush()

    def on_start(self):
        """
        Adds processing on start
        """
        sys.stdout.write(u"Type 'help' for guidance, or Ctl-C to exit.\n")
        sys.stdout.flush()

    def pull(self):
        """
        Fetches updates

        This function senses most recent item, and pushes it
        to the listening queue.

        """
        sys.stdout.write(self.prompt)
        sys.stdout.flush()

        try:
            line = next(self._lines)
            self.on_message({'text': line}, self.ears)
        except StopIteration:
            sys.stdout.write(u'^C\n')
            sys.stdout.flush()
            self.context.set('general.switch', 'off')

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
        message.mentioned_ids = [self.context.get('bot.id')]
        message.space_id = self.id

        queue.put(str(message))
