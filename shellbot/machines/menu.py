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

from .base import Machine


class Menu(Machine):
    """
    Menu who asks for some input

    Example::

        machine = Menu(bot=bot, question="1. Ok\n2. Ko", key="result.id")
        machine.start()
        ...


    """

    IS_MARKDOWN = 0
    IS_MANDATORY = 0
    RETRY_MESSAGE = u"Invalid input, please retry with the digit corresponding to your selection"
    ANSWER_MESSAGE = u"Ok, this has been noted"
    CANCEL_MESSAGE = u"Ok, forget about it"

    WAIT_DURATION = 20.0  # amount of time before being delayed
    CANCEL_DURATION = 40.0   # amount of time before being cancelled

    def on_init(self,
                question,
                options=[],
                on_retry=None,
                on_answer=None,
                on_cancel=None,
                is_mandatory=None,
                is_markdown=None,
                tip=None,
                timeout=None,
                key=None,
                prefix='machine',
                **kwargs):
        """
        Handles extended initialisation parameters

        :param question: The question to be asked in the chat room
        :type question: str

        :param options: The options to be proposed in the chat room
        :type options: list str

        :param on_retry: The message to ask for retry
        :type on_retry: str

        :param on_answer: The message on successful answer
        :type on_answer: str

        :param on_cancel: The message on overall cancellation
        :type on_cancel: str

        :param is_mandatory: The reply will be mandatory
        :type is_mandatory: boolean

        :param is_markdown: Indicate if it's markdown text
        :type is_markdown: boolean

        :param tip: Display the on_retry message after this delay in seconds
        :type tip: int

        :param timeout: Display the on_cancel message after this delay (0 for mandatory)
            in seconds
        :type timeout: int

        :param key: The label associated with saved data
        :type key: str

        :param prefix: the main keyword for configuration of this machine
        :type prefix: str

        """
        super(Menu, self).on_init(prefix, **kwargs)

        assert question not in (None, '')
        self.question = question

        assert options not in (None, '')
        self.options = options

        if on_retry in (None, ''):
            on_retry = self.RETRY_MESSAGE
        self.on_retry = on_retry

        if on_answer in (None, ''):
            on_answer = self.ANSWER_MESSAGE
        self.on_answer = on_answer

        if on_cancel in (None, ''):
            on_cancel = self.CANCEL_MESSAGE
        self.on_cancel = on_cancel

        if is_mandatory in (None,''):
            is_mandatory = self.IS_MANDATORY
        assert int(is_mandatory) >= 0
        self.is_mandatory = is_mandatory

        if is_markdown in (None,''):
            is_mardown = self.IS_MARKDOWN
        assert int(is_markdown) >= 0
        self.is_markdown = is_markdown

        if tip is not None:
            assert int(tip) > 0
            self.WAIT_DURATION = tip

        if timeout is not None:
            assert int(timeout) > 0
            assert self.CANCEL_DURATION > self.WAIT_DURATION
            self.CANCEL_DURATION = timeout

        self.key = key

        states = ['begin',
                  'waiting',
                  'delayed',
                  'end']

        transitions = [

            {'source': 'begin',
             'target': 'waiting',
             'action': self.ask},

            {'source': 'waiting',
             'target': 'end',
             'condition': lambda **z : self.get('answer') is not None,
             'action': self.stop},

            {'source': 'waiting',
             'target': 'delayed',
             'condition': lambda **z : self.elapsed > self.WAIT_DURATION,
             'action': lambda: self.say(self.on_retry),
            },

            {'source': 'delayed',
             'target': 'end',
             'condition': lambda **z : self.get('answer') is not None,
             'action': self.stop},

            {'source': 'delayed',
             'target': 'end',
             'condition': lambda **z : self.elapsed > self.CANCEL_DURATION,
             'action': self.cancel},

        ]

        self.build(states=states,
                   transitions=transitions,
                   initial='begin')

        self.start_time = time.time()

    @property
    def elapsed(self):
        """
        Measures time since the question has been asked
        """
        return time.time() - self.start_time

    def say(self,arguments):
        """
        say what has been requested
        """
        if self.is_markdown == 0:
            self.bot.say(arguments)
        else:
            self.bot.say(arguments,content=arguments)

    def ask(self):
        """
        Asks the question in the chat
        """
        lines = [self.question]
        i = 1
        for key in self.options:
           lines.append(u"{}. {}".format(i, key))
           i += 1
        self.say('\n'.join(lines))

        self.listen()
        self.start_time = time.time()

    def listen(self):
        """
        Listens for data received from the chat space

        This function starts a separate process to scan the
        ``bot.fan`` queue until time out.
        """
        p = Process(target=self.receive)
        p.daemon = True
        p.start()
        return p

    def receive(self):
        """
        Receives data from the chat space

        The loop is also stopped when the parameter ``general.switch``
        is changed in the context. For example::

            bot.context.set('general.switch', 'off')

        """
        logging.info(u"Receiving input")

        beginning = time.time()
        self.set('answer', None)
        try:
            while self.bot.context.get('general.switch', 'on') == 'on':

                if self.get('answer'):
                    break  # on good answer

                if not self.is_running:
                    break  # on machine stop

                if self.is_mandatory == 0: 
                    if time.time() - beginning > self.CANCEL_DURATION + 0.2:
                        break  # on cancellation limit

                try:
                    if self.bot.fan.empty():
                        self.bot.context.set('fan.stamp', time.time())
                        time.sleep(self.TICK_DURATION)
                        continue

                    item = self.bot.fan.get(True, self.TICK_DURATION)
                    if item is None:
                        break

                    logging.debug(u"Input has been received")
                    self.execute(arguments=item)

                except Exception as feedback:
                    logging.exception(feedback)
                    break

        except KeyboardInterrupt:
            pass

        logging.info(u"Receiver has been stopped")

    def execute(self, arguments):
        """
        Receives data from the chat
        """
        if arguments in (None, ''):
            self.say(self.on_retry)
            return

        arguments = self.filter(text=arguments)

        if arguments in (None, ''):
            self.say(self.on_retry)
            return

        self.set('answer', arguments)
        if self.key:
            self.bot.update('input', self.key, self.options[int(arguments)-1])

        self.say(self.on_answer.format(arguments))
        self.step(event='tick')

    def filter(self, text):
        """
        Filters data from user menu input

        Check if entry match with digit
        """
        try:
            assert int(text)
            assert int(text) <= len(self.options)
            assert int(text) > 0
        except Exception as feedback:
            return None
        return text

    def wait(self):
        """
        Wait input
        """
        
    def cancel(self):
        """
        Cancels the question
        """
        self.say(self.on_cancel)
        self.stop()
