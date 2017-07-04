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


class Input(Machine):
    """
    Asks for some input

    Example::

        machine = Input(bot=bot, question="PO Number?", key="order.id")
        machine.start()
        ...


    """
    IS_MARKDOWN = 0
    IS_MANDATORY = 0
    RETRY_MESSAGE = u"Invalid input, please retry"
    ANSWER_MESSAGE = u"Ok, this has been noted"
    CANCEL_MESSAGE = u"Ok, forget about it"

    WAIT_DURATION = 20.0  # amount of time before being delayed
    CANCEL_DURATION = 40.0   # amount of time before being cancelled

    def on_init(self,
                question,
                regex=None,
                mask=None,
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

        :param regex: The expected regex mask for the input (optional)
        :type regex: str

        :param mask: The expected mask for the input (optional)
        :type mask: str

        :param on_retry: The message to ask for retry
        :type on_retry: str

        :param on_answer: The message on successful answer
        :type on_answer: str

        :param on_cancel: The message on overall cancellation
        :type on_cancel: str

        :param is_mandatory: The reply will be mandatory
        :type is_mandatory: boolean

        :param is_markdown: Indicate if text is provided with markdown format
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

        If a mask is provided, it is used to check provided input.
        Use following conventions to build the mask:

        * ``A`` - Any kind of unicode symbol such as ``g`` or ``ç``
        * ``9`` - A digit such as ``0`` or ``2``
        * ``+`` - When following ``#`` or ``9``, indicates optional extensions
           of the same type
        * Any other symbol, including punctuation or white space, has to match
           exactly.

        For example:

        * ``9999A``  will match 4 digits and 1 additional character
        * ``#9-A+`` will match ``#3-June 2017``

        """
        super(Input, self).on_init(prefix, **kwargs)

        assert question not in (None, '')
        self.question = question

        self.regex = regex

        self.mask = mask

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
            is_markdown = self.IS_MARKDOWN
        assert int(is_markdown) >= 0
        self.is_markdown = is_markdown

        if tip is not None:
            assert int(tip) > 0
            self.WAIT_DURATION = tip

        if timeout is not None:
            assert int(timeout) >= 0
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
             'condition': lambda **z : self.elapsed > self.CANCEL_DURATION and self.is_mandatory == 0,
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

    def ask(self):
        """
        Asks the question in the chat
        """
        self.say(self.question)
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

    def say(self,arguments):
        """
        Say what is requested
        """
        if self.is_markdown == 0:
            self.bot.say(arguments)
        else:
            self.bot.say(arguments, content=arguments)

    def execute(self, arguments):
        """
        Receives data from the chat
        """
        if arguments in (None, ''):
            self.say(self_on_retry)
            return

        arguments = self.filter(text=arguments)

        if arguments in (None, ''):
            self.say(self.on_retry)
            return

        self.set('answer', arguments)
        if self.key:
            self.bot.update('input', self.key, arguments)

        self.say(self.on_answer.format(arguments))
        
        self.step(event='tick')

    def filter(self, text):
        """
        Filters data from user input

        If a mask is provided, this function uses it to extract data
        and to validate the presence of useful content.
        """

        if self.regex:
            return self.searchRegex(self.regex, text)


        if self.mask:
            return self.search(self.mask, text)
        return text

    def searchRegex(self, regex, text):
        """
        Searches with regex in text
        """
        assert regex not in (None, '')
        assert text not in (None, '')

        pattern = re.compile(regex, re.IGNORECASE)
        searched = pattern.search(text)
        if searched:
            return searched.group()

        return None


    def search(self, mask, text):
        """
        Searches for structured data in text
        """
        assert mask not in (None, '')
        assert text not in (None, '')

        mask = mask.replace('+', 'pLuS')
        mask = re.escape(mask)
        mask = mask.replace('pLuS', '+').replace('A', '\S').replace('9', '\d').replace('Z','[^0-9]')

        pattern = re.compile(mask, re.U)

        searched = pattern.search(text)

        if searched:
            return searched.group()

        return None

    def cancel(self):
        """
        Cancels the question
        """
        self.say(self.on_cancel)
        
        self.stop()
