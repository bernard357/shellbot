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
import sys
import yaml
import importlib

sys.path.insert(0, os.path.abspath('..'))


class Shell(object):
    """
    Parses input and reacts accordingly
    """

    def __init__(self, context, mouth=None, inbox=None):
        self.context = context
        self.mouth = mouth
        self.inbox = inbox

        self.commands = {}
        self.load_commands(context.get('shell.commands', []))

    @property
    def name(self):
        """
        Retrieves the dynamic name of this bot

        :return: The value of ``bot.name`` key in current context
        :rtype: str

        """
        return self.context.get('bot.name', 'Shelly')

    @property
    def version(self):
        """
        Retrieves the version of this bot

        :return: The value of ``bot.version`` key in current context
        :rtype: str

        """
        return self.context.get('bot.version', '*unknown*')

    def say(self, message):
        """
        Sends a response back from shell

        :param message: The message from the shell
        :type message: str

        """
        if self.mouth is not None:
            self.mouth.put(message)
        else:
            logging.info(str(message))

    def load_default_commands(self):
        """
        Loads default commands for this shell

        Example:
            >>>shell.load_default_commands()

        """
        labels = [
            'shellbot.commands.echo',
            'shellbot.commands.help',
            'shellbot.commands.noop',
            'shellbot.commands.sleep',
            'shellbot.commands.version',
        ]
        self.load_commands(labels)

    def load_commands(self, labels=[]):
        """
        Loads commands for this shell

        :param commands: A list of commands to load
        :type commands: List of labels

        Example:
            >>>commands = ['shellbot.commands.help']
            >>>shell.load_commands(commands)

        Each label should reference a python module that can be used
        as a command. Check ``base.py`` in ``shellbot.commands`` for
        a clear view of what it means to be a vaid command for this shell.
        """
        for label in labels:
            self.load_command(label)

    def load_command(self, label):
        """
        Loads one command for this shell

        :param command: A command to load
        :type command: str

        Example:
            >>>shell.load_commands('shellbot.commands.help')

        Label should reference a python module that can be used
        as a command. Check ``base.py`` in ``shellbot.commands`` for
        a clear view of what it means to be a vaid command for this shell.
        """
        try:
            module = importlib.import_module(label)
        except ImportError:
            (dummy, label) = label.split('.', 1)
            module = importlib.import_module(label)

        name = label.rsplit('.', 1)[1].capitalize()
        cls = getattr(module, name)
        command = cls(self)
        for key in self.commands.keys():
            if command.keyword == key:
                raise KeyError("Duplicate command '{}'".format(key))

        self.commands[ command.keyword ] = command

    def do(self, line):
        """
        Handles one line of text

        This function uses the first token as a verb, and looks for a command
        of the same name in the shell.

        If the command does not exist, an error message will be given back to
        the end user.
        """
        print("Handling: {}".format(line))
        tokens = line.split(' ')
        verb = tokens.pop(0)
        if len(verb) < 1:
            verb = 'help'

        if len(tokens) > 0:
            arguments = ' '.join(tokens)
        else:
            arguments = ''

        try:
            if verb in self.commands.keys():
                command = self.commands[verb]
                if command.is_interactive:
                    command.execute(arguments)
                else:
                    if not self.context.get('worker.busy', False):
                        self.say("Ok, working on it")
                    else:
                        self.say("Ok, will work on it as soon as possible")
                    self.inbox.put((command.keyword, arguments))

            else:
                self.say(
                    "Sorry, I do not know how to handle '{}'".format(verb))

        except Exception as feedback:
            raise

            self.say(
                "Sorry, I do not know how to handle '{}'".format(verb))
