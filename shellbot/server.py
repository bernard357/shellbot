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

import logging
from bottle import Bottle

from .context import Context


class Server(Bottle):
    """
    Serves web requests
    """

    def __init__(self,
                 context=None,
                 httpd=None,
                 route=None,
                 routes=None,
                 check=False):
        """
        Serves web requests

        :param context: global context for this process
        :type context: Context

        :param httpd: actual WSGI server

        :param route: a route to add to this instance
        :type route: Route

        :param routes: multiple routes to add to this instance
        :type routes: list of Route

        :param check: True to check configuration settings
        :type check: bool

        """
        self.context = Context() if context is None else context

        self.httpd = Bottle() if httpd is None else httpd

        self._routes = {}
        if route is not None:
            self.add_route(route)
        if routes is not None:
            self.add_routes(routes)

        if check:
            self.configure()

    def configure(self, settings={}):
        """
        Checks settings of the server

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        This function reads key ``server`` and below, and update
        the context accordingly::

            >>>shell.configure({'server': {
                   'binding': '10.4.2.5',
                   'port': 5000,
                   'debug': True,
                   }})

        This can also be written in a more compact form::

            >>>shell.configure({'server.port': 5000})

        """

        self.context.apply(settings)
        self.context.check('server.binding', '0.0.0.0')
        self.context.check('server.url', 'http://no.server', filter=True)
        self.context.check('server.port', 8080)
        self.context.check('server.debug', False)

    @property
    def routes(self):
        """
        Lists all routes

        :return: a list of routes, or []

        Example::

            >>>server.get_routes()
            ['/hello', '/world']
        """
        return sorted(self._routes.keys())

    def route(self, route):
        """
        Gets one route by path

        :return: the related route, or None
        """
        return self._routes.get(route, None)

    def add_routes(self, items):
        """
        Adds web routes

        :param routes: a list of additional routes
        :type routes: list of routes

        """
        for item in items:
            self.add_route(item)

    def add_route(self, item):
        """
        Adds one web route

        :param route: one additional route
        :type route: Route

        """
        self._routes[item.route] = item
        self.httpd.route(item.route, method="GET", callback=item.get)
        self.httpd.route(item.route, method="POST", callback=item.post)
        self.httpd.route(item.route, method="PUT", callback=item.put)
        self.httpd.route(item.route, method="DELETE", callback=item.delete)

    def run(self):
        """
        Serves requests
        """
        logging.info(u'Starting web server')

        for route in self.routes:
            logging.debug(u'- {}'.format(route))

        try:
            self.httpd.run(host=self.context.get('server.address', '0.0.0.0'),
                           port=self.context.get('server.port', 80),
                           debug=self.context.get('server.debug', False),
                           server='paste')
        except:
            pass

        logging.info(u'Web server has been stopped')
