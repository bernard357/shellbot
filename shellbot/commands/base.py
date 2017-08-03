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


class Command(object):
    """
    Implements one command
    """

    def __init__(self, engine=None, **kwargs):
        """
        Implements one command

        :param engine: the engine that is powering the bot
        :type engine: Engine

        """
        self.engine = engine
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.on_init()

    def on_init(self):
        """
        Handles extended initialisation

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_init(self):
                self.engine.register('stop', self)

        """
        pass

    def execute(self, bot, arguments=None, **kwargs):
        """
        Executes this command

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        The function is invoked with a variable number of arguments.
        Therefore the need for ``**kwargs``, so that your code is safe
        in all cases.

        The recommended signature for commands that handle textual arguments
        is the following:

        ```
        def execute(self, bot, arguments=None, **kwargs):
            ...
            if arguments:
                ...
        ```

        In this situation, ``arguments`` contains all text typed after the verb
        itself. For example, when the command ``magic`` is invoked with the
        string::

            magic rub the lamp

        then the related command instance is called like this::

            magic = shell.command('magic')
            magic.execute(bot, arguments='rub the lamp')

        For commands that can handle file attachments, you could use 
        following approach::

            def execute(self,
                        bot,
                        arguments=None,
                        attachment=None,
                        url=None,
                        **kwargs):
                ...
                if url:  # a document has been uploaded with this command
                    content = bot.space.download_attachment(url)
                    ...


        Reference information on parameters provided by the shell:

        - ``bot`` - This is the bot instance for which the command is
          executed. From this you can update the chat with ``bot.say()``, or
          access data attached to the bot in ``bot.store``. The engine and all
          global items can be access with ``bot.engine``.

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


        This function should report on progress by sending
        messages with one or multiple ``bot.say("Whatever response")``.

        """
        if self.information_message:
            bot.say(self.information_message)

    keyword = None          # verb or token for this command

    information_message = None    # basic information for this command

    usage_message = None    # usage information for this command

    is_hidden = False       # when command should not be listed by 'help'

    in_group = True         # when command can be used from group channels
    in_direct = True        # when command can be used from direct channels
