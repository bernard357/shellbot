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

from .base import Store
from .memory import MemoryStore
from .sqlite import SqliteStore

__all__ = [
    'Store',
    'MemoryStore',
    'SqliteStore',
]


class StoreFactory(object):
    """
    Builds a store from configuration

    Example::

        my_context = Context(settings={
            'sqlite': {
                'db': 'my_store.db',
            }
        })

        store = StoreFactory.build(context=my_context)

    """

    types = {
        'memory': MemoryStore,
        'sqlite': SqliteStore,
    }

    @classmethod
    def build(self, context, **kwargs):
        """
        Builds an instance based on provided configuration

        :param context: configuration to be used
        :type context: Context

        :return: a ready-to-use store
        :rtype: Store

        A ``ValueError`` is raised if no type could be identified.
        """
        assert context is not None

        type = self.sense(context)
        store = self.get(type, context=context, **kwargs)
        store.check()

        return store

    @classmethod
    def sense(self, context):
        """
        Detects type from configuration

        :param context: configuration to be analyzed
        :type context: Context

        :return: a guessed type
        :rtype: str

        Example::

            type = StoreFactory.sense(context)

        If no type can be identified, then ``memory`` is returned so that
        a minimum store can be loaded.
        """

        for type in sorted(self.types.keys()):
            if context.has(prefix=type):
                return type

        return 'memory'

    @classmethod
    def get(self, type, **kwargs):
        """
        Loads a store by type

        :param type: the required store
        :type type: str

        :return: a store instance

        This function seeks for a suitable store class in the library, and
        returns an instance of it.

        Example::

            store = StoreFactory.get('sqlite')

        A ``ValueError`` is raised if the type is unknown.
        """

        try:
            return self.types[type](**kwargs)

        except KeyError:
            raise ValueError(u"Unable to load store type {}".format(type))
