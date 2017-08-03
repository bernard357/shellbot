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

from builtins import str
import importlib
import logging
from multiprocessing import Process, Queue
from six import string_types

from shellbot.commands import Default


class Shell(object):
    """
    Parses input and reacts accordingly
    """

    def __init__(self, engine):
        """
        Parses input and reacts accordingly

        :param engine: the overarching engine
        :type engine: Engine

        """
        self.engine = engine
        self.engine.shell = self

        self._commands = {}

        self.line = None
        self.count = 0
        self.verb = None

    def configure(self, settings={}):
        """
        Checks settings of the shell

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``shell`` and below, and update
        the context accordingly::

            >>>shell.configure({'shell': {
                   'commands':
                      ['examples.exception.state', 'examples.exception.next']
                   }})

        This can also be written in a more compact form::

            >>>shell.configure({'shell.commands':
                   ['examples.exception.state', 'examples.exception.next']
                   })

        Note that this function does preserve commands that could have been
        loaded previously.
        """

        self.engine.context.apply(settings)
        self.engine.context.check('shell.commands', default=[])

        self.load_default_commands()
        self.load_commands(self.engine.get('shell.commands'))

    @property
    def commands(self):
        """
        Lists available commands

        :return: a list of verbs
        :rtype: list of str

        This function provides with a dynamic inventory of all capabilities
        of this shell.

        Example::

            >>>print(shell.commands)
            ['*default', '*empty', 'help']
        """
        return sorted(self._commands.keys())

    def command(self, keyword):
        """
        Get one command

        :param keyword: the keyword for this command
        :type keyword: str

        :return: the instance for this command
        :rtype: command or None

        Lists available commands and related usage information.

        Example::

            >>>print(shell.command('help').information_message)

        """
        return self._commands.get(keyword, None)

    def load_default_commands(self):
        """
        Loads default commands for this shell

        Example::

            >>>shell.load_default_commands()

        """
        labels = [
            'shellbot.commands.default',
            'shellbot.commands.echo',
            'shellbot.commands.empty',
            'shellbot.commands.help',
            'shellbot.commands.noop',
            'shellbot.commands.sleep',
            'shellbot.commands.upload',
            'shellbot.commands.version',
        ]
        self.load_commands(labels)

    def load_commands(self, commands=[]):
        """
        Loads commands for this shell

        :param commands: A list of commands to load
        :type commands: List of labels or list of commands

        Example::

            >>>commands = ['shellbot.commands.help']
            >>>shell.load_commands(commands)

        Each label should reference a python module that can be used
        as a command. Check ``base.py`` in ``shellbot.commands`` for
        a clear view of what it means to be a vaid command for this shell.

        If objects are provided, they should duck type the command defined
        in ``base.py`` in ``shellbot.commands``.

        Example::

            >>>from shellbot.commands.version import Version
            >>>version = Version()
            >>>from shellbot.commands.help import Help
            >>>help = Help()
            >>>shell.load_commands([version, help])
        """
        for item in commands:
            self.load_command(item)

    def load_command(self, command):
        """
        Loads one command for this shell

        :param command: A command to load
        :type command: str or command

        If a string is provided, it should reference a python module that can
        be used as a command. Check ``base.py`` in ``shellbot.commands`` for
        a clear view of what it means to be a vaid command for this shell.

        Example::

            >>>shell.load_command('shellbot.commands.help')

        If an object is provided, it should duck type the command defined
        in ``base.py`` in ``shellbot.commands``.

        Example::

            >>>from shellbot.commands.version import Version
            >>>command = Version()
            >>>shell.load_command(command)
        """
        if isinstance(command, string_types):
            try:
                module = importlib.import_module(command)
                logging.debug(u"Loading command '{}'".format(command))
            except ImportError:
                logging.error(u"Unable to import '{}'".format(command))
                return

            name = command.rsplit('.', 1)[1].capitalize()
            cls = getattr(module, name)
            command = cls(self.engine)

        command.engine = self.engine

        if command.keyword in self._commands.keys():
            logging.debug(u"Command '{}' has been replaced".format(
                command.keyword))

        self._commands[command.keyword] = command

    def do(self, line, received=None):
        """
        Handles one line of text

        :param line: a line of text to parse and to handle
        :type line: str

        :param received: the message that contains the command
        :type received: Message

        This function uses the first token as a verb, and looks for a command
        of the same name in the shell.

        If the command does not exist, the command ``*default`` is used
        instead. Default behavior is implemented in
        ``shellbot.commands.default`` yet you can load a different command
        for customization.

        If an empty line is provided, the command ``*empty`` is triggered.
        Default implementation is provided in ``shellbot.commands.empty``.

        When a file has been uploaded, the information is given to the
        command that is executed. If no message is provided with the file, the
        command ``*upload`` is triggered instad of ``*empty``.
        Default implementation is provided in ``shellbot.commands.upload``.

        Following parameters are used for the execution of a command:

        - ``bot`` - A bot instance is retrieved from the channel id mentioned
          in ``received``, and provided to the command.

        - ``arguments`` - This is a string that contains everything after the
          command verb. When ``hello How are you doing?`` is submitted to the
          shell, ``hello`` is the verb, and ``How are you doing?`` are the
          arguments. This is the regular case. If there is no command ``hello``
          then the command ``*default`` is used instead, and arguments provided
          are the full line ``hello How are you doing?``.

        - ``attachment`` - When a file has been uploaded, this attribute
          provides its external name, e.g., ``picture024.png``. This can be used
          in the executed command, if you keep in mind that the same name can be
          used multiple times in a conversation.

        - ``url`` - When a file has been uploaded, this is the handle by which
          actual content can be retrieved. Usually, ask the underlying space
          to get a local copy of the document.

        """
        line = str(line) if line else ''  # sanity check

        logging.info(u"Handling: {}".format(line))
        self.line = line
        self.count += 1

        tokens = line.split(' ')
        verb = tokens.pop(0)
        if len(verb) < 1:
            if received and received.url:
                verb = '*upload'
            else:
                verb = '*empty'

        kwargs = {}

        if len(tokens) > 0:
            kwargs['arguments'] = ' '.join(tokens)
        else:
            kwargs['arguments'] = ''

        if received and received.attachment:
            kwargs['attachment'] = received.attachment

        if received and received.url:
            kwargs['url'] = received.url

        channel_id = received.channel_id if received else None
        bot = self.engine.get_bot(channel_id)

        if bot.channel is None:
            return

        try:
            if verb in self._commands.keys():
                command = self._commands[verb]

                if ( (command.in_direct and bot.channel.is_direct)
                    or (command.in_group and not bot.channel.is_direct) ):

                    self.verb = verb
                    command.execute(bot, **kwargs)

                else:

                    logging.debug(u"- command cannot be used in this channel")
                    bot.say(u"Sorry, I do not know how to handle '{}'".format(verb))

            elif '*default' in self._commands.keys():
                kwargs['arguments'] = line  # provide full input line
                command = self._commands['*default']
                command.execute(bot, **kwargs)

            else:
                bot.say(u"Sorry, I do not know how to handle '{}'".format(verb))

        except Exception:
            bot.say(u"Sorry, I do not know how to handle '{}'".format(verb))
            raise
