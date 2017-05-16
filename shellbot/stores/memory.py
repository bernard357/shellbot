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

import colorlog
import logging
import os
from multiprocessing import Lock, Manager

from .base import Store


class MemoryStore(Store):
    """
    Stores data for one space

    This is a key-value store, that supports concurrency
    across multiple processes.

    Example::

        store = MemoryStore()

    """

    def on_init(self, **kwargs):
        """
        Adds processing to initialization
        """
        self.values = Manager().dict()

    def _set(self, key, value):
        """
        Sets a permanent value

        :param key: name of the value
        :type key: str

        :param value: actual value
        :type value: any serializable type is accepted

        This functions stores or updates a value in the back-end storage
        system.

        Example::

            store._set('parameter_123', 'George')

        """
        self.values[key] = value

    def _get(self, key):
        """
        Gets a permanent value

        :param key: name of the value
        :type key: str

        :return: the actual value, or None

        Example::

            value = store._get('parameter_123')

        """
        return self.values.get(key)

    def _clear(self, key=None):
        """
        Forgets a value or all values

        :param key: name of the value to forget, or None
        :type key: str

        To clear only one value, provide the name of it.
        For example::

            store._clear('parameter_123')

        To clear all values in the store, just call the function
        without a value.
        For example::

            store._clear()

        """
        if key in (None, ''):
            self.values.clear()
        else:
            self.values[key] = None
