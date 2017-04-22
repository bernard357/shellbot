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


class NoQueue(object):
    def put(self, item=None):
        raise Exception(u"No queue for this notification")


class Notify(Route):
    """
    Notifies a queue on web request

    >>>queue = Queue()
    >>>route = Notify(route='/notify', queue=queue, notification='hello')

    When the route is requested over the web, the notification is pushed
    to the queue.

    >>>queue.get()
    'hello'

    Notification is triggered on GET, POST, PUT and DELETE verbs.
    """

    route = '/notify'

    queue = NoQueue()

    notification = None

    def get(self, **kwargs):
        logging.debug(u"GET {}".format(self.route))
        return self.notify()

    def post(self):
        logging.debug(u"POST {}".format(self.route))
        return self.notify()

    def put(self):
        logging.debug(u"PUT {}".format(self.route))
        return self.notify()

    def delete(self):
        logging.debug(u"DELETE {}".format(self.route))
        return self.notify()

    def notify(self):
        item = self.notification if self.notification else self.route
        self.queue.put(item)
        return 'OK'
