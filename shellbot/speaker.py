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
from Queue import Empty
from six import string_types
import time


class Speaker(object):
    """
    Sends updates to a business messaging space
    """

    def __init__(self, mouth, space):
        """
        Sends updates to a business messaging space

        :param mouth: the queue of outbound updates
        :type mouth: queue

        :param space: the connector to a business messaging space
        :type space: SparkSpace or similar

        """
        self.mouth = mouth
        self.space = space

    def work(self, context):
        """
        Continuously send updates

        :param context: the context shared across processes
        :type context: context

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            space = SparkSpace(context=context)
            speaker = Speaker(mouth=mouth, space=space)

            process = Process(target=speaker.work, args=(context,))
            process.daemon = True
            process.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            context.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            mouth.put(Exception('EOQ'))

        Note that items are not picked up from the queue until the underlying
        space is ready for handling messages.
        """
        logging.info(u"Starting speaker")

        self.context = context

        try:
            self.context.set('speaker.counter', 0)
            while self.context.get('general.switch', 'on') == 'on':

                if not self.space.is_ready:
                    logging.debug(
                        u"Speaker is waiting for space to be ready...")
                    time.sleep(5)
                    continue

                try:
                    item = self.mouth.get(True, 0.1)
                    if isinstance(item, Exception):
                        break
                    counter = self.context.increment('speaker.counter')
                    self.process(item, counter)
                except Empty:
                    pass

        except KeyboardInterrupt:
            pass

        logging.info(u"Speaker has been stopped")

    def process(self, item, counter):
        """
        Sends one update to a business messaging space

        :param item: the update to be transmitted
        :type item: str or dict

        :param counter: number of items processed so far
        :type counter: int

        """

        logging.debug(u'Speaker is working on {}'.format(counter))

        if self.space is not None:
            if isinstance(item, string_types):
                self.space.post_message(item)
            else:
                self.space.post_message(item.message,
                                        markdown=item.markdown,
                                        file_path=item.file)
        else:
            logging.info(str(item))
