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

from .base import Space
from .local import LocalSpace
from .ciscospark import SparkSpace

__all__ = [
    'SpaceFactory',
    'Space',
    'LocalSpace',
    'SparkSpace',
]


class SpaceFactory(object):
    """
    Builds a space from configuration

    Example::

        context = Context(settings={
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        bot = ShellBot(context=context)
        space = SpaceFactory.build(bot)

    """

    types = {
        'space': Space,
        'local': LocalSpace,
        'spark': SparkSpace,
    }

    @classmethod
    def build(self, bot, **kwargs):
        """
        Builds an instance based on provided configuration

        :param bot: configuration to be used
        :type bot: ShellBot

        :return: a ready-to-use space
        :rtype: Space

        A ``ValueError`` is raised if no type could be identified.
        """
        assert bot is not None

        type = self.sense(bot.context)
        space = self.get(type, bot=bot, **kwargs)
        space.configure()

        return space

    @classmethod
    def sense(self, context):
        """
        Detects type from configuration

        :param context: configuration to be analyzed
        :type context: Context

        :return: a guessed type
        :rtype: str

        Example::

            type = SpaceFactory.sense(context)

        A ``ValueError`` is raised if no type could be identified.
        """

        for type in sorted(self.types.keys()):
            if context.has(prefix=type):
                return type

        raise ValueError(
            u"No space type could be identified from configuration")

    @classmethod
    def get(self, type, **kwargs):
        """
        Loads a space by type

        :param type: the required space
        :type type: str

        :return: a space instance

        This function seeks for a suitable space class in the library, and
        returns an instance of it.

        Example::

            space = SpaceFactory.get('spark', ex_token='123')

        A ``ValueError`` is raised if the type is unknown.
        """

        try:
            return self.types[type](**kwargs)

        except KeyError:
            raise ValueError(u"Unable to load space type {}".format(type))
