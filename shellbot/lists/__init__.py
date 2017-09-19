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

        This function looks for the key ``lists`` and below in the
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

        Note that list names are all put to lower case internally, for easy
        subsequent references. With the previous examples, you can
        retrieve the first list with `The Famous Four` or with
        `the famous four`. This is spacially convenient for lists used
        as commands, when invoked from a mobile device.

        """
        settings = self.context.get('lists', [])

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

            name = name.lower()  # align across chat devices

            self.lists[name] = self.build_list(attributes)

    def build_list(self, attributes):
        """
        Builds one list

        Example in YAML::

            - name: The Famous Four
              as_command: true
              items:
                - alice@acme.com
                - bob@project.org
                - celine@secret.mil
                - dude@bangkok.travel

        The ``as_command`` parameter is a boolean that indicates if the list
        can be used as a shell command. When ``as_command`` is set to true,
        the named list appears in the list of shell commands. Members of the
        list are added to a channel when the name of the list is submitted to
        the shell.
        """
        assert isinstance(attributes, dict)

        items = attributes.get('items', [])
        list = List(items=items)
        list.name = attributes.get('name')
        list.as_command = attributes.get('as_command', False)
        return list

    def get_list(self, name):
        """
        Gets a named list

        :param name: Name of the target list
        :type name: str

        :return: an iterator

        An empty list is returned when the name is unknown.

        Example use case, where an alert is sent to members of a team::

            for person in factory.get_list('SupportTeam'):
                number = get_phone_number(person)
                send_sms(important_message, number)
        """
        if name:
            name = name.lower()  # align across chat devices

        return self.lists.get(name, [])

    def list_commands(self):
        """
        Lists items that can be invoked as shell commands

        :return: an iterator of list names
        """

        for name in self.lists.keys():
            list = self.lists[name]
            if list.as_command:
                yield list.name

    def apply_to_list(self, name, apply):
        """
        Handles each item of a named list

        :param name: designates the list to use
        :type name: str

        :param apply: the function that is applied to each item
        :type apply: callable

        This function calls the provided function for each item of a named
        list.

        For example, you could write an alerting system like this::

            def alert(person):
                number = get_phone_number(person)
                send_sms(important_message, number)

            factory.apply_to_list('SupportTeam', alert)

        Lambda functions are welcome as well. For example, this can be useful
        for the straightforward addition of participants to a given bot::

            factory.apply_to_list(name='SupportTeam',
                                  apply=lambda x: my_bot.add_participant(x))

        """
        for item in self.get_list(name):
            apply(item)
