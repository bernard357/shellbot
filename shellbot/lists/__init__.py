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

from shellbot import Context
from .base import List


__all__ = [
    'List',
    'ListFactory',
]


class ListFactory(object):
    """
    Manages named lists

    Example::

        factory = ListFactory(context=my_context)
        factory.configure()
        ...
        my_list = factory.get_list('The Famous Four')

    """
    def __init__(self, context=None):
        self.context = context if context else Context()

        self.lists = {}

    def configure(self):
        """
        Loads lists as defined in context

        This function looks for the key ``general.lists`` and below in the
        context, and creates a dictionary of named lists.

        Example configuration in YAML format::

            lists:

                - name: The Famous Four
                  items:
                    - alice@acme.com
                    - bob@project.org
                    - celine@secret.mil
                    - dude@bangkok.travel

                - name: Support Team
                  items:
                    - service.desk@acme.com
                    - supervisor@brother.mil

        """
        settings = self.context.get('general.lists', [])

        for attributes in settings:

            if not isinstance(attributes, dict):
                logging.warning(u"Found a list that is not a dictionary")
                logging.debug(u"- {}".format(str(attributes)))
                continue

            name = attributes.get('name')
            if not name:
                logging.warning(u"Missing attribute 'name' in list")
                logging.debug(u"- {}".format(str(attributes)))
                continue

            self.lists[name] = self.build_list(attributes)

    def build_list(self, attributes):
        """
        Builds one list

        Example in YAML::

            - name: The Famous Four
              items:
                - alice@acme.com
                - bob@project.org
                - celine@secret.mil
                - dude@bangkok.travel

        """
        assert isinstance(attributes, dict)

        items = attributes.get('items', [])
        return List(items=items)

    def get_list(self, name):
        """
        Gets a named list

        :param name: Name of the target list
        :type name: str

        :return: list

        An empty list is returned when the name is unknown.
        """
        return self.lists.get(name, [])
