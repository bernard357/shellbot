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

from .base import Route


class Wrap(Route):
    """
    Calls a function on web request

    When the route is requested over the web, the target function is
    called.

    Example::

        def my_callable(**kwargs):
            ...

        route = Wrap(callable=my_callable, route='/hook')

    Wrapping is triggered on GET, POST, PUT and DELETE verbs.
    """

    route = None

    callable = None

    def get(self, **kwargs):
        if self.callable is None:
            raise NotImplementedError()
        logging.debug(u"GET {}".format(self.route))
        return self.callable(**kwargs)

    def post(self):
        if self.callable is None:
            raise NotImplementedError()
        logging.debug(u"POST {}".format(self.route))
        return self.callable()

    def put(self):
        if self.callable is None:
            raise NotImplementedError()
        logging.debug(u"PUT {}".format(self.route))
        return self.callable()

    def delete(self):
        if self.callable is None:
            raise NotImplementedError()
        logging.debug(u"DELETE {}".format(self.route))
        return self.callable()
