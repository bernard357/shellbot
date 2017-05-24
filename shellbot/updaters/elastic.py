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

from builtins import str
from elasticsearch import Elasticsearch, ConnectionError
import logging
import os
from six import string_types
import sys
import time

from .base import Updater


class ElasticsearchUpdater(Updater):
    """
    Writes inbound events to Elasticsearch

    An event may be a Message, an Attachment, a Join or Leave notification,
    or any other Event.

    Updaters expose a filtering function that can be connected to the
    inbound flow of events handled by the Listener.

    Example::

        updater = ElasticsearchUpdater(host='db.local:9200')
        listener = Listener(filter=updater.filter)

    """

    def on_init(self, host=None, index=None, **kwargs):
        """
        Writes inbound events to Elasticsearch
        """
        self.host = host
        self.index = index if index not in (None, '') else 'shellbot'

    def get_host(self):
        """
        Provides the Elasticsearch host

        :rtype: str
        """
        if self.host not in (None, ''):
            return self.host

        return self.bot.get('elasticsearch.updater.host', 'localhost:9200')

    def on_bond(self):
        """
        Creates index on space bonding
        """
        self.db = Elasticsearch(
            [self.get_host()],
            )

        try:
            self.db.indices.create(index=self.index, ignore=400) # may exist
        except ConnectionError as feedback:
            logging.error('- unable to connect')
            raise

    def put(self, event):
        """
        Processes one event

        :param event: inbound event
        :type event: Event or Message or Attachment or Join or Leave

        The function writes the event as a JSON document in Elasticsearch.
        """
        logging.debug("- updating Elasticsearch")
        result = self.db.index(index=self.index,
                               doc_type='event',
                               body=event.attributes)
