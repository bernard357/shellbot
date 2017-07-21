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

import logging
from multiprocessing import Process, Queue
import os
from six import string_types
import sys
import time

from shellbot.channel import Channel
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

    def on_init(self, prefix='space', input=None, **kwargs):
        """
        Handles extended initialisation parameters

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        :param input: Lines of text to be submitted to the chat
        :type input: str or list of str

        Example::

            space = LocalSpace(context=context, prefix='local.audit')

        Here we create a new local space, and use
        settings under the key ``local.audit`` in the context of this bot.

        Example::

            space = LocalSpace(input='hello world')

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

    def check(self):
        """
        Check settings

        This function reads key ``local`` and below, and update
        the context accordingly.

        This function also selects the right input for this local space.
        If some content has been provided during initialisation, it is used
        to simulate user input. Else stdin is read one line at a time.
        """
        logging.debug(u"Context: {}".format(self.context.values))
        self.context.check(self.prefix+'.title', 'Local space', filter=True)
        self.context.check(self.prefix+'.moderators', [], filter=True)
        self.context.check(self.prefix+'.participants', [], filter=True)

        self.context.set('server.binding', None)  # no web server at all

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

    def create(self, title, **kwargs):
        """
        Creates a channel

        :param title: title of the new channel
        :type title: str

        :return: Channel

        This function returns a representation of the local channel.

        """
        assert title not in (None, '')
        attributes = {
            'id': '*local',
            'title': title,

        }
        return Channel(attributes)

    def get_by_title(self, title, **kwargs):
        """
        Looks for an existing channel by title

        :param title: title of the target channel
        :type title: str

        :return: Channel instance or None

        """
        assert title not in (None, '')
        attributes = {
            'id': '*local',
            'title': title,

        }
        return Channel(attributes)

    def get_by_id(self, id, **kwargs):
        """
        Looks for an existing channel by id

        :param id: identifier of the target channel
        :type id: str

        :return: Channel instance or None

        """
        assert id not in (None, '')
        attributes = {
            'id': id,
            'title': self.configured_title(),

        }
        return Channel(attributes)

    def update(self, channel, **kwargs):
        """
        Updates an existing channel

        :param channel: a representation of the updated channel
        :type channel: Channel

        """
        pass

    def delete(self, id, **kwargs):
        """
        Deletes a channel

        :param id: the unique id of an existing channel
        :type id: str

        """
        pass

    def add_moderator(self, id, person):
        """
        Adds one moderator

        :param id: the unique id of an existing channel
        :type id: str

        :param person: e-mail address of the person to add
        :type person: str

        """
        self.moderators.append(person)

    def add_participant(self, id, person):
        """
        Adds one participant

        :param id: the unique id of an existing channel
        :type id: str

        :param person: e-mail address of the person to add
        :type person: str

        """
        self.participants.append(person)

    def remove_participant(self, id, person):
        """
        Removes one participant

        :param id: the unique id of an existing channel
        :type id: str

        :param person: e-mail address of the person to remove
        :type person: str

        """
        self.participants.remove(person)

    def post_message(self,
                     id,
                     text=None,
                     content=None,
                     file=None,
                     **kwargs):
        """
        Posts a message

        :param id: the unique id of an existing channel
        :type id: str

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as MArkdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        Example message out of plain text::

        >>>space.post_message(id=id, text='hello world')

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
        message.space_id = '*local'

        logging.debug(u"- putting message to ears")
        queue.put(str(message))
