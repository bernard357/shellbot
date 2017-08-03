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
from multiprocessing import Manager, Process, Queue
import re
import time

from .input import Input


class Menu(Input):
    """
    Selects among multiple options

    This implements a state machine that can capture a choice
    from chat participants. It can ask a question, wait for some input,
    check provided data and provide guidance when needed.

    Example::

        machine = Menu(bot=bot,
                       question="What would you prefer?",
                       options=["Some starter and then main course",
                                "Main course and sweety dessert"])
        machine.start()
        ...

        if machine.get('answer') == 1:
            prepare_appetizer()
            prepare_main_course()

        if machine.get('answer') == 2:
            prepare_main_course()
            prepare_some_cake()

    In normal operation mode, the machine asks a question in the chat space,
    then listen for an answer, captures it, and stops.

    When no adequate answer is provided, the machine will provide guidance
    in the chat space after some delay, and ask for a retry. Multiple retries
    can take place, until correct input is provided, or the machine is
    timed out.

    The machine can also time out after a (possibly) long duration, and send
    a message in the chat space when giving up.

    If correct input is mandatory, no time out will take place and the machine
    will really need a correct answer to stop.

    Data that has been captured can be read from the machine itself.
    For example::

        value = machine.get('answer')

    If the machine is given a key, this is used for feeding the bot store.
    For example::

        machine.build(key='my_field', ...)
        ...

        value = bot.recall('input')['my_field']

    The most straightforward way to process captured data in real-time
    is to subclass ``Menu``, like in the following example::

        class MyMenu(Menu):

            def on_input(self, value):
                do_something_with(value)

        machine = MyMenu(...)
        machine.start()


    """

    RETRY_MESSAGE = u"Invalid input, please enter your choice as a number"

    def on_init(self,
                options=[],
                **kwargs):
        """
        Selects among multiple options

        :param question: Message to ask for some input (mandatory)
        :type question: str

        :param options: The options of the menu
        :type options: list of str

        :param on_answer: Message on successful data capture
        :type on_answer: str

        :param on_answer_content: Rich message on successful data capture
        :type on_answer_content: str in Markdown or HTML format

        :param on_answer_file: File to be uploaded on successful data capture
        :type on_answer_file: str

        :param on_retry: Message to provide guidance and ask for retry
        :type on_retry: str

        :param on_retry_content: Rich message on retry
        :type on_retry_content: str in Markdown or HTML format

        :param on_retry_file: File to be uploaded on retry
        :type on_retry_file: str

        :param retry_delay: Repeat the on_retry message after this delay in seconds
        :type retry_delay: int

        :param on_cancel: Message on time out
        :type on_cancel: str

        :param on_cancel_content: Rich message on time out
        :type on_cancel_content: str in Markdown or HTML format

        :param on_cancel_file: File to be uploaded on time out
        :type on_cancel_file: str

        :param is_mandatory: If the bot will insist and never give up
        :type is_mandatory: boolean

        :param cancel_delay: Give up on this input after this delay in seconds
        :type cancel_delay: int

        :param key: The label associated with data captured in bot store
        :type key: str

        """
        super(Menu, self).on_init(**kwargs)

        assert options not in (None, '')
        assert len(options) > 0
        self.options = options

        assert self.mask is None  # not supported
        assert self.regex is None  # not supported

    def ask(self):
        """
        Asks which menu option to select

        If a bare question is provided, then text is added to list
        all available options.

        If a rich question is provided, then we assume that it also
        contains a representation of menu options and displays it 'as-is'.

        """
        text = self.question if self.question else None

        if text:
            index = 1
            text += '\n'
            for option in self.options:
                text += u"{}. {}\n".format(index, option)
                index += 1

        self.bot.say(text)

        content = self.question_content if self.question_content else None

        if content:
            self.bot.say(content=content)

        self.start_time = time.time()
        self.listen()

    def filter(self, text):
        """
        Filters data from user input

        :param text: Text coming from the chat space
        :type text: str

        :return: Text of the selected option, or None

        """
        try:
            assert int(text) > 0
            assert int(text) <= len(self.options)
            return self.options[int(text)-1]
        except Exception:
            return None
