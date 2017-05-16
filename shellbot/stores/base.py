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

import json
import logging
import os
from multiprocessing import Lock


class Store(object):
    """
    Stores data for one space

    This is a key-value store, that supports concurrency
    across multiple processes.

    Configuration of the storage engine is coming from settings of the overall
    bot.

    Example::

        store = Store(bot=bot)

    Normally a store is related to one single space. For this, you can use the
    function ``bond()`` to set the space unique id.

    Example::

        store.bond(id=space.id)

    Once this is done, the store can be used to remember and to recall values.

    Example::

        store.remember('gauge', gauge)
        ...
        gauge = store.recall('gauge')

    """

    def __init__(self, bot=None, **kwargs):
        """
        Stores data for one space

        :param bot: the overarching bot
        :type bot: ShellBot

        """
        self.bot = bot

        self.lock = Lock()

        self.on_init(**kwargs)

    def on_init(self, **kwargs):
        """
        Adds processing to initialization

        This function should be expanded in sub-class, where necessary.

        This function is the right place to capture additional parameters
        provided on instance initialisation.

        Example::

            def on_init(self, prefix='sqlite', **kwargs):
                ...

        """
        pass

    def check(self):
        """
        Checks configuration

        This function should be expanded in sub-class, where necessary.

        This function is the right place to check parameters that can be used
        by this instance.

        Example::

            def check(self):
                self.bot.context.check(self.prefix+'.db', 'store.db')

        """
        pass

    def bond(self, id=None):
        """
        Creates or uses resource required for the permanent back-end

        :param id: the unique identifier of the related space
        :type id: str

        This function should be expanded in sub-class, where necessary.

        This function is the right place to create files, databases, and index
        that can be necessary for a store back-end.

        Example::

            def bond(self, id=None):
                db.execute("CREATE TABLE ...
        """
        pass

    def to_text(self, value):
        """
        Turns a value to a textual representation

        :param value: a python object that can be serialized
        :type value: object

        :return: a textual representation that can be saved in store
        :rtype: str

        Here we use ``json.dumps()`` to do the job. You can override
        this function in your subclass if needed.
        """
        return json.dumps(value)

    def from_text(self, textual):
        """
        Retrieves a value from a textual representation

        :param textual: a textual representation that can be saved in store
        :type textual: str

        :return: a python object
        :rtype: object or None

        Here we use ``json.loads()`` to do the job. You can override
        this function in your subclass if needed.
        """
        try:
            return json.loads(textual)
        except TypeError:
            return None

    def remember(self, key, value):
        """
        Remembers a value

        :param key: name of the value
        :type key: str

        :param value: actual value
        :type value: any serializable type is accepted

        This functions stores or updates a value in the back-end storage
        system.

        Example::

            store.remember('parameter_123', 'George')

        This function is safe on multiprocessing and multithreading.

        """
        self.lock.acquire()
        try:
            self._set(key, self.to_text(value))
        finally:
            self.lock.release()

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

        This function should be expanded in sub-class.

        Example::

            def _set(self, key, value):
                db.update(self.id, key, value)
                ...

        """
        raise NotImplementedError()

    def recall(self, key, default=None):
        """
        Recalls a value

        :param key: name of the value
        :type key: str

        :param default: default value
        :type default: any serializable type is accepted

        :return: the actual value, or the default value, or None

        Example::

            value = store.recall('parameter_123')

        This function is safe on multiprocessing and multithreading.

        """
        self.lock.acquire()
        value = None
        try:
            value = self.from_text(self._get(key))

            if value is None:  # when value remembered was None
                value = default
        finally:
            self.lock.release()
            return value

    def _get(self, key):
        """
        Gets a permanent value

        :param key: name of the value
        :type key: str

        :return: the actual value, or None

        Example::

            value = store._get('parameter_123')

        This function should be expanded in sub-class, where necessary.

        Example::

            def _get(self, key):
                value = db.select(self.id, key)
                ...

        """
        raise NotImplementedError()

    def forget(self, key=None):
        """
        Forgets a value or all values

        :param key: name of the value to forget, or None
        :type key: str

        To clear only one value, provides the name of it.
        For example::

            store.forget('parameter_123')

        To clear all values in the store, just call the function
        without a value.
        For example::

            store.forget()

        This function is safe on multiprocessing and multithreading.

        """
        self.lock.acquire()
        try:
            self._clear(key)
        finally:
            self.lock.release()

    def _clear(self, key=None):
        """
        Forgets a value or all values

        :param key: name of the value to forget, or None
        :type key: str

        To clear only one value, provides the name of it.
        For example::

            store._clear('parameter_123')

        To clear all values in the store, just call the function
        without a value.
        For example::

            store._clear()

        This function should be expanded in sub-class, where necessary.

        Example::

            def forget(self, key):
                db.delete(key)
                ...

        """
        raise NotImplementedError()

    def increment(self, key, delta=1):
        """
        Increments a value

        :param key: name of the value
        :type key: str

        :param delta: increment to apply
        :type delta: int

        :return: the new value

        Example::

            value = store.increment('gauge')

        """
        self.lock.acquire()
        value = 0
        try:
            value = self.from_text(self._get(key))
            if not isinstance(value, int):
                value = 0
            value += delta
            self._set(key, self.to_text(value))
        finally:
            self.lock.release()
            return value

    def decrement(self, key, delta=1):
        """
        Decrements a value

        :param key: name of the value
        :type key: str

        :param delta: decrement to apply
        :type delta: int

        :return: the new value

        Example::

            value = store.decrement('gauge')

        """
        self.lock.acquire()
        try:
            value = self.from_text(self._get(key))
            if not isinstance(value, int):
                value = 0
            value -= delta
            self._set(key, self.to_text(value))
        finally:
            self.lock.release()
            return value

    def append(self, key, item):
        """
        Appends an item to a list

        :param key: name of the list
        :type key: str

        :param item: a new item to append
        :type item: any serializable type is accepted

        Example::

            >>>store.append('names', 'Alice')
            >>>store.append('names', 'Bob')
            >>>store.recall('names')
            ['Alice', 'Bob']

        """
        self.lock.acquire()
        try:
            value = self.from_text(self._get(key))
            if not isinstance(value, list):
                value = []
            value.append(item)
            self._set(key, self.to_text(value))
        finally:
            self.lock.release()

    def update(self, key, label, item):
        """
        Updates a dict

        :param key: name of the dict
        :type key: str

        :param label: named entry in the dict
        :type label: str

        :param item: new value of this entry
        :type item: any serializable type is accepted

        Example::

            >>>store.update('input', 'PO Number', '1234A')
            >>>store.recall('input')
            {'PO Number': '1234A'}

        """
        assert label not in (None, '')

        self.lock.acquire()
        try:
            value = self.from_text(self._get(key))
            if not isinstance(value, dict):
                value = {}
            value[label] = item
            self._set(key, self.to_text(value))
        finally:
            self.lock.release()
