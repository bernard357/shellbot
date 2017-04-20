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
from multiprocessing import Lock, Manager


class Context(object):
    """
    Stores data across multiple independent processing units

    This is a basic key-value store, that supports concurrency
    across multiple processes
    """

    def __init__(self, settings=None):
        self.lock = Lock()
        self.values = Manager().dict()

        if settings:
            self.apply(settings)

    def apply(self, settings={}):
        """
        Applies multiple settings at once
        """

        self.lock.acquire()
        try:
            for key in settings.keys():
                if isinstance(settings[key], dict):
                    for label in settings[key].keys():
                        self.values[key+'.'+label] = settings[key].get(label)
                elif len(key.split('.')) > 1:
                    self.values[key] = settings[key]
                else:
                    self.values['general.'+key] = settings[key]
        finally:
            self.lock.release()

    def check(self,
              key,
              default=None,
              is_mandatory=False,
              validate=None):
        """
        Checks some settings

        :param key: the key that has to be checked
        :type primary: str

        :param default: the default value if no statement can be found
        :type default: str

        :param is_mandatory: raise an exception if keys are not found
        :type is_mandatory: bool

        :param validate: a function called to validate values before the import
        :type validate: callable

        Example::

            context = Context({
                'spark': {
                    'room': 'My preferred room',
                    'moderators':
                        ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                    'participants':
                        ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                    'team': 'Anchor team',
                    'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY>',
                    'webhook': "http://73a1e282.ngrok.io",
                }
            })

            context.check('spark.room', is_mandatory=True)
            context.check('spark.team')

        When a default value is provided, it is used to initialize
        properly some key.

        >>>context.check('general.switch', 'on')

        Another usage is to ensure that a key has been set previously.

        >>>context.check('spark.room', is_mandatory=True)

        Additional control can be added with the validation function.

        >>>context.check('general.switch',
        ...              validate=lambda x: x in ('on', 'off'))

        This function raises ``KeyError`` if a mandatory key is absent.
        If a validation function is provided, then a ``ValueError`` can be
        raised as well in some situations.
        """
        self.lock.acquire()
        try:

            if default is not None:
                value = self.values.get(key, None)
                if value is None:
                    self.values[key] = default
                    value = default

            elif (is_mandatory or validate):
                try:
                    value = self.values[key]
                except KeyError:
                    raise KeyError(u"Missing '{}' in context".format(key))

            if validate and validate(value) is False:
                raise ValueError(
                    u"Invalid value for '{}' in context".format(key))

        finally:
            self.lock.release()

    def get(self, key, default=None):
        """
        Retrieves the value of one key
        """

        self.lock.acquire()
        value = None
        try:
            value = self.values.get(key, default)

            if value is None:
                value = default
        finally:
            self.lock.release()
            return value

    def set(self, key, value):
        """
        Remembers the value of one key
        """

        self.lock.acquire()
        try:
            self.values[key] = value
        finally:
            self.lock.release()

    def increment(self, key, delta=1):
        """
        Increments a value
        """

        self.lock.acquire()
        try:
            value = self.values.get(key, 0)
            if not isinstance(value, int):
                value = 0
            value += delta
            self.values[key] = value
        finally:
            self.lock.release()
            return value

    def decrement(self, key, delta=1):
        """
        Decrements a value
        """

        self.lock.acquire()
        try:
            value = self.values.get(key, 0)
            if not isinstance(value, int):
                value = 0
            value -= delta
            self.values[key] = value
        finally:
            self.lock.release()
            return value

    @classmethod
    def set_logger(cls, level=logging.DEBUG):
        """
        Configure logging

        :param level: expected level of verbosity

        This utility function should probably be put elsewhere
        """
        handler = colorlog.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            "%(asctime)-2s %(log_color)s%(message)s",
            datefmt='%H:%M:%S',
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        handler.setFormatter(formatter)

        logging.getLogger('').handlers = []
        logging.getLogger('').addHandler(handler)

        logging.getLogger('').setLevel(level=level)
