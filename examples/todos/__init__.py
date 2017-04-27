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

from .done import Done
from .drop import Drop
from .history import History
from .next import Next
from .todo import Todo
from .todos import Todos

__all__ = [
    'Done',
    'Drop',
    'History',
    'Next',
    'Todo',
    'Todos',
    'TodoFactory',
]

class TodoFactory(object):

    @classmethod
    def commands(self):
        return [Done(), Drop(), History(), Next(), Todo(), Todos()]

    def __init__(self, items=[], **kwargs):
        self.items = items
        self.archive = []

    def create(self, label):
        self.items.append(label)

    def read(self, index=1):
        try:
            return self.items[index-1]
        except:
            return None

    def update(self, index, label):
        try:
            self.items[index-1] = label
        except:
            pass

    def delete(self, index=1):
        try:
            self.items.pop(index-1)
        except:
            pass

    def complete(self, index=1):
        try:
            self.archive.append(self.items.pop(index-1))
        except:
            pass

    def parse(self, arguments):
        tokens = arguments.split(' ')
        token = tokens[0]
        if len(token) > 1 and token[0] == '#':
            token = token[1:]

        try:
            index = int(token)
            if index < 1 or index > len(self.items):
                return None
            return index
        except:
            return None
