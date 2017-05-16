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
import sqlite3

from .base import Store


class SqliteStore(Store):
    """
    Stores data for one space

    This is a basic permanent key-value store.

    Example::

        store = SqliteStore(db='shellstore.db', id=space.id)

    """

    def on_init(self,
                prefix='sqlite',
                id=None,
                db=None,
                **kwargs):
        """
        Adds processing to initialization

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        :param id: the unique identifier of the related space (optional)
        :type id: str

        :param db: name of the file that contains Sqlite data (optional)
        :type db: str

        Example::

            store = SqliteStore(bot=bot, prefix='sqlite')

        Here we create a new store powered by Sqlite, and use
        settings under the key ``sqlite`` in the context of this bot.
        """
        assert prefix not in (None, '')
        self.prefix = prefix
        self.id = id if id else '*id'

        if db not in (None, ''):
            self.bot.context.set(self.prefix+'.db', db)

    def check(self):
        """
        Checks configuration
        """
        self.bot.context.check(self.prefix+'.db', 'store.db')

    def get_db(self):
        """
        Gets a handle on the database
        """
        db = self.bot.context.get(self.prefix+'.db', 'store.db')
        return sqlite3.connect(db)

    def bond(self, id=None):
        """
        Creates or uses a file to store data

        :param id: the unique identifier of the related space
        :type id: str

        """
        if id not in (None, ''):
            self.id = id

        handle = self.get_db()
        try:
            handle.execute("CREATE TABLE store \
                (id INTEGER PRIMARY KEY, \
                context TEXT, \
                key TEXT UNIQUE, \
                value TEXT)")
        except sqlite3.OperationalError as feedback:
            logging.debug(feedback)

    def _set(self, key, value, handle=None):
        """
        Sets a permanent value

        :param key: name of the value
        :type key: str

        :param value: actual value
        :type value: any serializable type is accepted

        :param handle: an optional instance of a Sqlite database
        :type handle: a connection

        This functions stores or updates a value in the back-end storage
        system.

        Example::

            store._set('parameter_123', 'George')

        """
        handle = handle if handle else self.get_db()

        cursor = handle.cursor()
        cursor.execute("DELETE FROM store WHERE context=? AND key=?",
                       (self.id, key))
        cursor.execute("INSERT INTO store (context,key,value) VALUES (?,?,?)",
                       (self.id, key, value))
        handle.commit()
        cursor.close()

    def _get(self, key, handle=None):
        """
        Gets a permanent value

        :param key: name of the value
        :type key: str

        :param handle: an optional instance of a Sqlite database
        :type handle: a connection

        :return: the actual value, or None

        Example::

            value = store._get('parameter_123')

        """
        handle = handle if handle else self.get_db()

        cursor = handle.cursor()
        cursor.execute("SELECT value FROM store WHERE context=? AND key=?",
                       (self.id, key))
        result = cursor.fetchone()
        try:
            return result[0]
        except TypeError:
            return None

    def _clear(self, key=None, handle=None):
        """
        Forgets a value or all values

        :param key: name of the value to forget, or None
        :type key: str

        :param handle: an optional instance of a Sqlite database
        :type handle: a connection

        To clear only one value, provide the name of it.
        For example::

            store._clear('parameter_123')

        To clear all values in the store, just call the function
        without a value.
        For example::

            store._clear()

        """
        handle = handle if handle else self.get_db()

        if key in (None, ''):
            cursor = handle.cursor()
            cursor.execute("DELETE FROM store WHERE context=?",
                           (self.id,))
            handle.commit()
            cursor.close()

        else:
            cursor = handle.cursor()
            cursor.execute("DELETE FROM store WHERE context=? AND key=?",
                           (self.id, key))
            handle.commit()
            cursor.close()
