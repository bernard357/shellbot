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

    This implements a state machine that can get one piece of input
    from chat participants. It can ask a question, wait for some input,
    check provided data and provide guidance when needed.

    Example::

        machine = Input(bot=bot, question="PO Number?", key="order.id")
        machine.start()
        ...

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
    is to subclass ``Input``, like in the following example::

        class MyInput(Input):

            def on_input(self, value):
                mail.send_message(value)

        machine = MyInput(...)
        machine.start()

    """
    ANSWER_MESSAGE = u"Ok, this has been noted"
    RETRY_MESSAGE = u"Invalid input, please retry"
    CANCEL_MESSAGE = u"Ok, forget about it"

    RETRY_DELAY = 20.0  # amount of seconds between retries
    CANCEL_DELAY = 40.0   # amount of seconds before time out

    def on_init(self,
                question=None,
                question_content=None,
                mask=None,
                regex=None,
                on_answer=None,
                on_answer_content=None,
                on_answer_file=None,
                on_retry=None,
                on_retry_content=None,
                on_retry_file=None,
                retry_delay=None,
                on_cancel=None,
                on_cancel_content=None,
                on_cancel_file=None,
                cancel_delay=None,
                is_mandatory=False,
                key=None,
                **kwargs):
        """
        Asks for some input

        :param question: Message to ask for some input
        :type question: str

        :param question_content: Rich message to ask for some input
        :type question_content: str

        :param mask: A mask to filter the input
        :type mask: str

        :param regex: A regular expression to filter the input
        :type regex: str

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


        If a mask is provided, it is used to filter provided input.
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

        Alternatively, you can provide a regular expression (regex) to extract
        useful information from the input.

        You can use almost every regular expression that is supported
        by python. If parenthesis are used, the function returns the first
        matching group.

        For example, you can capture an identifier with a given prefix::

            machine.build(question="What is the identifier?",
                          regex=r'ID-\d\w\d+', ...)
            ...

            id = machine.filter('The id is ID-1W27 I believe')
            assert id == 'ID-1W27'

        As a grouping example, you can capture a domain name by asking for
        some e-mail address like this::

            machine.build(question="please enter your e-mail address",
                          regex=r'@([\w.]+)', ...)
            ...

            domain_name = machine.filter('my address is foo.bar@acme.com')
            assert domain_name == 'acme.com'

        """
        assert question not in (None, '') or question_content not in (None, '')
        self.question = question
        self.question_content = question_content

        assert regex is None or mask is None  # use only one of them
        self.regex = regex
        self.mask = mask

        self.on_answer = on_answer
        self.on_answer_content = on_answer_content
        self.on_answer_file = on_answer_file

        self.on_retry = on_retry
        self.on_retry_content = on_retry_content
        self.on_retry_file = on_retry_file

        self.on_cancel = on_cancel
        self.on_cancel_content = on_cancel_content
        self.on_cancel_file = on_cancel_file

        assert is_mandatory in (True, False)
        self.is_mandatory = is_mandatory

        if retry_delay is not None:
            assert float(retry_delay) > 0
            self.RETRY_DELAY = float(retry_delay)

        if cancel_delay is not None:
            assert float(cancel_delay) > 0
            self.CANCEL_DELAY = float(cancel_delay)
            assert self.CANCEL_DELAY > self.RETRY_DELAY

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
             'condition': lambda **z : self.elapsed > self.RETRY_DELAY,
             'action': self.say_retry,
            },

            {'source': 'delayed',
             'target': 'end',
             'condition': lambda **z : self.get('answer') is not None,
             'action': self.stop},

            {'source': 'delayed',
             'target': 'end',
             'condition': lambda **z : self.elapsed > self.CANCEL_DELAY and not self.is_mandatory,
             'action': self.cancel},

        ]

        during = {
            'begin': self.on_inbound,
            'waiting': self.on_inbound,
            'delayed': self.on_inbound,
            'end': self.on_inbound,
        }
        self.build(states=states,
                   transitions=transitions,
                   initial='begin')

        self.start_time = time.time()

    @property
    def elapsed(self):
        """
        Measures time since the question has been asked

        Used in the state machine for repeating the question and on time out.
        """
        return time.time() - self.start_time

    def say_answer(self, input):
        """
        Responds on correct capture

        :param input: the text that has been noted
        :type input: str

        """
        text = self.on_answer.format(input) if self.on_answer else None
        content = self.on_answer_content.format(input) if self.on_answer_content else None
        file = self.on_answer_file if self.on_answer_file else None

        if text in (None, '') and content in (None, ''):
            text = self.ANSWER_MESSAGE.format(input)

        self.bot.say(text)

        if content or file:
            self.bot.say(' ',
                         content=content,
                         file=file)

    def say_retry(self):
        """
        Provides guidance on retry

        """
        text = self.on_retry if self.on_retry else None
        content = self.on_retry_content if self.on_retry_content else None
        file = self.on_retry_file if self.on_retry_file else None

        if text in (None, '') and content in (None, ''):
            text = self.RETRY_MESSAGE

        self.bot.say(text)

        if content or file:
            self.bot.say(' ',
                         content=content,
                         file=file)

    def say_cancel(self):
        """
        Says that input has been timed out

        """
        text = self.on_cancel if self.on_cancel else None
        content = self.on_cancel_content if self.on_cancel_content else None
        file = self.on_cancel_file if self.on_cancel_file else None

        if text in (None, '') and content in (None, ''):
            text = self.CANCEL_MESSAGE

        self.bot.say(text)

        if content or file:
            self.bot.say(' ',
                         content=content,
                         file=file)

    def ask(self):
        """
        Asks the question in the chat space

        """

        text = self.question if self.question else None
        content = self.question_content if self.question_content else None

        self.bot.say(text)

        if content:
            self.bot.say(' ',
                         content=content)

        self.start_time = time.time()
        self.listen()

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

        This function implements a loop until some data has been
        actually captured, or until the state machine stops for some reason.

        The loop is also stopped when the parameter ``general.switch``
        is changed in the context. For example::

            engine.set('general.switch', 'off')

        """
        logging.info(u"Receiving input")

        self.set('answer', None)
        try:
            while self.bot.engine.get('general.switch', 'on') == 'on':

                if self.get('answer'):
                    break  # on good answer

                if not self.is_running:
                    break  # on machine stop

                try:
                    if self.bot.fan.empty():
                        label = 'fan.' + self.bot.id
                        self.bot.engine.set(label, time.time())
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

        logging.info(u"Input receiver has been stopped")

    def execute(self, arguments=None, **kwargs):
        """
        Receives data from the chat

        :param arguments: data captured from the chat space
        :type arguments: str

        This function checks data that is provided, and provides guidance
        if needed. It can extract information from the provided mask
        or regular expression, and save it for later use.
        """
        if arguments in (None, ''):
            self.say_retry()
            return

        arguments = self.filter(text=arguments)

        if arguments in (None, ''):
            self.say_retry()
            return

        # store at machine level
        self.set('answer', arguments)

        # store at bot level
        if self.key:
            self.bot.update('input', self.key, arguments)

        # use the input in this instance as well
        self.on_input(value=arguments, **kwargs)

        # advertise subscribers
        if self.key:
            self.bot.publisher.put(
                self.bot.id,
                {'from': self.bot.id,
                 'input': {'key': self.key, 'value': arguments}})

        self.say_answer(arguments)

        self.step(event='tick')

    def filter(self, text):
        """
        Filters data from user input

        :param text: Text coming from the chat space
        :type text: str

        :return: Data to be captured, or None

        If a mask is provided, or a regular expression, they are used
        to extract useful information from provided data.

        Example to read a PO mumber::

            machine.build(mask='9999A', ...)
            ...

            po = machine.filter('PO Number is 2413v')
            assert po == '2413v'

        """

        if self.mask:
            return self.search_mask(self.mask, text)

        if self.regex:
            return self.search_expression(self.regex, text)

        return text

    def search_mask(self, mask, text):
        """
        Searches for structured data in text

        :param mask: A simple expression to be searched
        :type mask: str

        :param text: The string from the chat space
        :type text: str

        :return: either the matching expression, or None

        Use following conventions to build the mask:

        * ``A`` - Any kind of unicode symbol, such as ``g`` or ``ç``
        * ``9`` - A digit, such as ``0`` or ``2``
        * ``+`` - When following ``#`` or ``9``, indicates optional extensions
           of the same type
        * Any other symbol, including punctuation or white space, has to match
           exactly.

        Some mask examples:

        * ``9999A``  will match 4 digits and 1 additional character
        * ``#9-A+`` will match ``#3-June 2017``

        Example to read a PO mumber::

            machine.build(question="What is the PO number?",
                          mask='9999A', ...)
            ...

            po = machine.filter('PO Number is 2413v')
            assert po == '2413v'

        """
        assert mask not in (None, '')
        assert text not in (None, '')

        logging.debug(u"Searching for mask '{}'".format(mask))
        mask = mask.replace('+', 'pLuS')
        mask = re.escape(mask)
        mask = mask.replace('pLuS', '+').replace('A', '\S').replace('9', '\d').replace('Z','[^0-9]')
        logging.debug(u"- translated to expression '{}'".format(mask))

        pattern = re.compile(mask, re.U)
        searched = pattern.search(text)
        if not searched:
            logging.debug(u"- no match")
            return None

        matched = searched.group()
        logging.debug(u"- found '{}'".format(matched))
        return matched

    def search_expression(self, regex, text):
        """
        Searches for a regular expression in text

        :param regex: A regular expression to be matched
        :type regex: str

        :param text: The string from the chat space
        :type text: str

        :return: either the matching expression, or None

        You can use almost every regular expression that is supported
        by python. If parenthesis are used, the function returns the first
        matching group.

        For example, you can capture an identifier with a given prefix::

            machine.build(question="What is the identifier?",
                          regex=r'ID-\d\w\d+', ...)
            ...

            id = machine.filter('The id is ID-1W27 I believe')
            assert id == 'ID-1W27'

        As a grouping example, you can capture a domain name by asking for
        some e-mail address like this::

            machine.build(question="please enter your e-mail address",
                          regex=r'@([\w.]+)', ...)
            ...

            domain_name = machine.filter('my address is foo.bar@acme.com')
            assert domain_name == 'acme.com'

        """
        assert regex not in (None, '')
        assert text not in (None, '')

        logging.debug(u"Searching for expression '{}'".format(regex))
        pattern = re.compile(regex, re.I)
        searched = pattern.search(text)
        if not searched:
            logging.debug(u"- no match")
            return None

        matched = searched.group()
        if len(searched.groups()) > 0:  # return the first matching group
            matched = searched.groups()[0]
        logging.debug(u"- found '{}'".format(matched))
        return matched

    def on_input(self, value, **kwargs):
        """
        Processes input data

        :param value: data that has been captured
        :type value: str

        This function is called as soon as some input has been captured.
        It can be overlaid in subclass, as in the following example::

            class MyInput(Input):

                def on_input(self, value):
                    mail.send_message(value)

            machine = MyInput(...)
            machine.start()

        The extra parameters wil be used in case of attachment with
        the value.
        """
        pass

    def on_inbound(self, **kwargs):
        """
        Updates the chat on inbound message

        """
        if kwargs.get('event') != 'inbound':
            return
        logging.debug(u"Receiving inbound message")

        message = kwargs('message')
        self.bot.say(u"Received {}: {} (from {})".format(message['input']['key'],
                                                    message['input']['value'],
                                                    message['from']))

    def cancel(self):
        """
        Cancels the question

        Used by the state machine on time out
        """
        self.say_cancel()
        self.stop()
