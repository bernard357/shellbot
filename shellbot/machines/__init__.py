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

class MachineFactory(object):
    """
    Provides new state machines

    In simple situations, you can rely on standard machines, and provide any
    parameters by these. For example::

        factory = MachineFactory(module='shellbot.machines.input'
                                 question="What's Up, Doc?")

        ...

        machine = factory.get_machine()

    When you provide different state machines for direct channels and for
    group channels, overlay member functions as in this example::

        class GreatMachineForDirectChannel(Machine):
            ...

        class MachineOnlyForGroup(Machine):
            ...

        class MyFactory(MachineFactory):

            def get_machine_for_direct_channel(self, bot):
                return GreatMachineForDirectChannel( ... )

            def get_machine_for_group_channel(self, bot):
                return MachineOnlyForGroup( ... )

    """

    def __init__(self, module=None, name=None, **kwargs):
        """
        Provides new state machines

        :param module: The python module to import
        :type module: str

        :param name: The class name to instantiate (optional)
        :type name: str

        If no name is provided, than we use the last part of the module instead.

        Other parameters are given to the instantiated object.

        Example::

            factory = MachineFactory('shellbot.machines.input')
            machine = factory.get_machine()   # Input()


        Example::

            factory = MachineFactory('shellbot.machines.base', 'Machine')
            machine = factory.get_machine()   # Machine()

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

            my_machine = factory.get_machine(bot=my_bot)
            my_machine.start()

        This function detects the kind of channel that is associated with this
        bot, and provides a suitable state machine.
        """
        if bot and bot.channel and bot.channel.is_direct:
            return self.get_machine_for_direct_channel(bot)

        elif bot and bot.channel and bot.channel.is_group:
            return self.get_machine_for_group_channel(bot)

        else:
            return self.get_default_machine(bot)

    def get_machine_for_direct_channel(self, bot):
        """
        Gets a new state machine for a direct channel

        :param bot: The bot associated with this state machine
        :type bot: ShellBot

        Example::

            my_machine = factory.get_machine_for_direct_channel(bot=my_bot)
            my_machine.start()

        This function can be overlaid in a subclass for adapting
        the production of state machines for direct channels.
        """
        return self.get_machine_from_class(bot=bot,
                                           module=self.module,
                                           name=self.name,
                                           **self.parameters)

    def get_machine_for_group_channel(self, bot):
        """
        Gets a new state machine for a group channel

        :param bot: The bot associated with this state machine
        :type bot: ShellBot

        Example::

            my_machine = factory.get_machine_for_group_channel(bot=my_bot)
            my_machine.start()

        This function can be overlaid in a subclass for adapting
        the production of state machines for group channels.
        """
        return self.get_machine_from_class(bot=bot,
                                           module=self.module,
                                           name=self.name,
                                           **self.parameters)

    def get_default_machine(self, bot):
        """
        Gets a new state machine

        :param bot: The bot associated with this state machine
        :type bot: ShellBot

        Example::

            my_machine = factory.get_default_machine(bot=my_bot)
            my_machine.start()

        This function can be overlaid in a subclass for adapting
        the production of state machines for default case.
        """
        return self.get_machine_from_class(bot=bot,
                                           module=self.module,
                                           name=self.name,
                                           **self.parameters)

    def get_machine_from_class(self, bot, module, name, **kwargs):
        """
        Gets a new state machine from a module

        :param bot: The bot associated with this state machine
        :type bot: ShellBot

        :param module: The python module to import
        :type module: str

        :param name: The class name to instantiate (optional)
        :type name: str

        Example::

            machine = factory.get_machine_from_class(my_bot,
                                                     'shellbot.machines.base',
                                                     'Machine')

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
        return cls(bot, **kwargs)
