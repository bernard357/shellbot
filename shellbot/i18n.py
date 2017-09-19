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

class Customization(object):
    """
    Changes static strings used by shellbot

    Throughout the full shellbot code the function ``_()`` is used for
    both internationalization and for customization.
    """

    def __init__(self, context=None):
        """
        Changes static strings used by shellbot

        :param context: the settings of this engine

        """
        self.context = context
        self.actual_strings = {}  # cache of strings used by shellbot

    def _(self, text):
        """
        Returns a customized string

        :param text: string used in the source code
        :return: customized string

        """

        customized = self.actual_strings.get(text)
        if customized:
            return customized

        if self.context:
            customized = self.context.get('customized.'+text, text)
        else:
            customized = text

        self.actual_strings[text] = customized  # cache for next lookup
        return customized

customization = Customization()

def _(text):
    """
    The default behavior is to not change strings at all
    """
    return customization._(text)
