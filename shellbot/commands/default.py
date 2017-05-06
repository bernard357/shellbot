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

from multiprocessing import Lock

from .base import Command


class Default(Command):
    """
    Handles unmatched command

    This is also the right place to catch all user input that is not a command.
    """

    keyword = u'*default'
    information_message = u'Handle unmatched command'
    is_hidden = True

    default_message = u"Sorry, I do not know how to handle '{}'"

    lock = Lock()
    _call_once = None
    _callback = None

    def execute(self, arguments):
        """
        Handles unmatched command

        Arguments provided should include all of the user input, including
        the first token that has not been recognised as a valid command.
        """
        self.lock.acquire()
        try:
            if self._call_once:
                callable = self._call_once
                self._call_once = None

            elif self._callback:
                callable = self._callback

            else:
                callable = self.bot.say
                arguments = self.default_message.format(arguments)

        finally:
            self.lock.release()

        callable(arguments)

    def call_once(self, callable):
        """
        Arms a callback to be used only once

        This function is useful to capture user responses.

        Example::

            def save_answer(arguments):
                context.set('po_number', arguments)

            default = shell.command('*default')
            default.call_once(save_answer)
            shell.say("What is the order number please?")

        If you change your mind, you can provide the value None.

        Example::

            default.call_once(None)

        """
        self.lock.acquire()
        try:
            if callable:
                assert self._call_once is None  # should not be called twice
            self._call_once = callable

        finally:
            self.lock.release()

    def callback(self, callable):
        """
        Defers processing to another place

        This function is useful to add natural language processing to the bot.

        Example::

            nlp_engine = Engine(...)

            default = shell.command('*default')
            default.callback(nlp_engine.on_input)

        If you change your mind, you can provide the value None.

        Example::

            default.callback(None)

        """
        self.lock.acquire()
        try:
            if callable:
                assert self._callback is None  # should not be called twice
            self._callback = callable

        finally:
            self.lock.release()

