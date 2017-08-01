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

from .base import Command


class Upload(Command):
    """
    Handles a bare file upload
    """

    keyword = u'*upload'
    information_message = u'Handle file upload'
    is_hidden = True

    feedback_message = u"Thank you for the information shared!"

    def execute(self, bot, attachment, url, arguments=None, **kwargs):
        """
        Handles bare upload

        :param bot: The bot for this execution
        :type bot: Shellbot

        :param attachment: External name of the uploaded file
        :type attachment: str

        :param url: The link to fetch actual content
        :type url: str

        :param arguments: The arguments for this command
        :type arguments: str or ``None``

        """
        bot.say(self.feedback_message.format(attachment))
