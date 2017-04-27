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
import os
from six import string_types
import sys
import importlib

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context


class Step(object):
    """
    Represents a step in a linear process
    """

    def __init__(self, attributes, index):
        """
        Represents a step in a linear process

        :param attributes: the dict to use
        :type attributes: dict

        :param index: index of this step
        :type index: int

        """
        self.label = attributes.get('label', u'Step {}'.format(index))
        self.message = attributes.get('message',
                                      u'(no description is available)')
        self.markdown = attributes.get('markdown', None)
        self.moderators = attributes.get('moderators', [])
        if isinstance(self.moderators, string_types):
            self.moderators = [self.moderators]
        self.participants = attributes.get('participants', [])
        if isinstance(self.participants, string_types):
            self.participants = [self.participants]


class Steps(object):
    """
    Handles successive steps in a linear process
    """

    def __init__(self,
                 context=None,
                 configure=False):
        """
        Handles successive steps in a linear process

        :param context: global context for this process
        :type context: Context

        :param configure: True to check configuration settings
        :type configure: bool

        """
        self.context = context if context else Context()

        if configure:
            self.configure()

    def configure(self, settings={}):
        """
        Checks settings of the machine

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``process.steps`` and below, and update
        the context accordingly.

        In the example below, the machine handles a process with 4
        successive steps::

            shell.configure({

                'process.steps': [

                    {
                        'label': u'Level 1',
                        'message': u'Initial capture of information',
                    },

                    {
                        'label': u'Level 2',
                        'message': u'Escalation to technical experts',
                        'moderators': 'alice@acme.com',
                    },

                    {
                        'label': u'Level 3',
                        'message': u'Escalation to decision stakeholders',
                        'participants': 'bob@acme.com',
                    },

                    {
                        'label': u'Terminated',
                        'message': u'Process is closed, yet conversation can continue',
                    },

                ]

            })

        """

        self.context.apply(settings)
        self.context.check('process.steps', [])
        self._index = None

    @property
    def step(self):
        """
        Gets current step

        :return: current step, or None
        """
        if self._index is None:
            return None

        steps = self.context.get('process.steps', [])

        if self._index < len(steps):
            return Step(attributes=steps[self._index], index=self._index)

        return None

    def next(self):
        """
        Moves to next step

        :return: current step, or None
        """
        steps = self.context.get('process.steps', [])

        if len(steps) < 1:
            return None

        if self._index is None:
            self._index = 0
        elif self._index < len(steps)-1:
            self._index += 1

        return Step(attributes=steps[self._index], index=self._index)
