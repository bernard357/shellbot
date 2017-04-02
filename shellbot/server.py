#!/usr/bin/env python
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

        print('Using prefix {}'.format(prefix))
        self.app.route('/'+prefix+'/hello/<name>', callback=self.hello)

    def start(self):
        print('Starting web server')
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
