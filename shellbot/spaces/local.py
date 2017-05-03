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
import time

from .base import Space


class LocalSpace(Space):
    """
    Handles chat locally

    This little class allows developers to test their commands interface
    locally, without the need for a real API back-end.

    Example::

        space = LocalSpace()
        space.post_message('Hello, World!')

    """

    def on_init(self, **kwargs):
        """
        Adds processing to space initialisation
        """
        self.moderators = []
        self.participants = []

    def check(self):
        """
        Checks that valid settings are available
        """
        self.bot.context.check(self.prefix+'.title', is_mandatory=True)
        self.bot.context.check(self.prefix+'.moderators', [])
        self.bot.context.check(self.prefix+'.participants', [])

    def on_bond(self):
        """
        Adds processing to space bond
        """
        self.post_message('Connected locally')

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
                     **kwargs):
        """
        Posts a message

        :param text: content of the message is plain text
        :type text: str

        Example message out of plain text::

        >>>space.post_message(text='hello world')

        """
        print(text)
