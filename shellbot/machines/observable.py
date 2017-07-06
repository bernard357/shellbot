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

class Event(object):
    pass

class Observable(object):
    """
    Implements observable method to be used for callback

    Example::
        def callback_func(event):
            self.bot.say('that is my callback')

        observe = Observable()
        observe.subscribe(callback_func)

    """

    def __init__(self):
        self.callbacks = []

    def subscribe(self, bot, callback):
        self.bot = bot
        logging.debug('Callback subscription: ' + str(callback))
        self.callbacks.append(callback)

    def fire(self, **attrs):
        for k, v in attrs.iteritems():
            setattr(e, k, v)
        for fn in self.callbacks:
            logging.debug('Callback fire: ' + str(fn))
            fn(self)
