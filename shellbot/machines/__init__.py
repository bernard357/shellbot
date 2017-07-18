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

import importlib
import logging

from .base import Machine, State, Transition
from .input import Input
from .sequence import Sequence
from .steps import Steps
from .menu import Menu

__all__ = [
    'Input',
    'Machine',
    'Sequence',
    'Steps',
    'Menu',
]

class MachinesFactory(object):
    """
    Provides new state machines

    Example::

        factory = MachinesFactory(module='shellbot.machines.input'
                                  question="What's Up, Doc?")

        ...

        machine = factory.get_machine()

    """

    def __init__(self, module=None, name=None, **kwargs):
        """
        Provides new state machines

        :param module: The python module to import
        :type module: str

        :param name: The class name to instantiate
        :type name: str

        Other parameters are given to the instantiated object.
        """
        self.module = module
        self.name = name
        self.parameters = kwargs if kwargs else {}

    def get_machine(self, bot=None):
        """
        Gets a new state machine

        :param bot: The bot associated with this state machine
        :type bot: ShellBot

        Example::

            my_machine = factory.get(bot=my_bot)
            my_machine.start()

        """
        assert self.module not in (None, '')  # need python module name
        try:
            handle = importlib.import_module(self.module)
            logging.debug(u"Loading machine '{}'".format(self.module))
        except ImportError:
            logging.error(u"Unable to import '{}'".format(self.module))
            return None

        if not self.name:
            self.name = self.module.rsplit('.', 1)[1].capitalize()
        cls = getattr(handle, self.name)
        return cls(bot, **self.parameters)
