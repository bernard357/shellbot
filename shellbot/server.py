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

import json
import logging
import os
from multiprocessing import Process, Queue
import requests
from requests_toolbelt import MultipartEncoder
import sys
import time
from bottle import Bottle, request, template

from context import Context
from shell import Shell


class Server(Bottle):

    def __init__(self, context, shell):
        self.context = context
        self.shell = shell
        self.app = Bottle()

    def route(self, prefix):
        self.app.route('/', method="GET", callback=self.index)

        print(u'Using prefix {}'.format(prefix))
        self.app.route('/'+prefix+'/hello/<name>', callback=self.hello)

    def start(self):
        print(u'Starting web server')
        self.route(self.context.get('server.prefix', '12357'))
        self.app.run(host=self.context.get('server.address', '0.0.0.0'),
                     port=self.context.get('server.port', 80),
                     debug=self.context.get('server.debug', False),
                     server='paste')

    def index(self):
        """
        Provides the home page
        """
        return "Hello World"

    def hello(self, name="Guest"):
        return template('Hello {{name}}, how are you?', name=name)

# the program launched from the command line
#
if __name__ == "__main__":

    context = Context()
    context.set('server.port', 8080)
    context.set('server.debug', True)

    mouth = Queue()
    inbox = Queue()
    shell = Shell(context, mouth, inbox)
    shell.load_default_commands()

    server = Server(context=context, shell=shell)
    server.start()
