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
import time


class List(object):
    """
    Implements an immutable list

    This allows easy integration of external reference data such
    as list of e-mail addresses, etc.

    """

    def __init__(self,
                 bot=None,
                 **kwargs):
        """
        Implements an immutable list

        :param bot: the overarching bot
        :type bot: ShellBot

        """
        self.bot = bot

        self.on_init(**kwargs)

    def on_init(self, items=[], **kwargs):
        """
        Handles extended initialisation parameters

        :param items: a list of items
        :type items: list or set

        Example::

            list = List(items=['a', 'b', 'c'])
            for item in list:
                ...

        This function should be expanded in sub-class, where necessary.

        """
        self.items = items

    def __iter__(self):
        """
        Returns a generator for this list

        This function should be expanded in sub-class, where necessary.

        """
        for item in self.items:
            yield item
