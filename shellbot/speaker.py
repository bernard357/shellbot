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
from multiprocessing import Process
from six import string_types
import time


class Vibes(object):
    def __init__(self,
                 text=None,
                 content=None,
                 file=None,
                 channel_id=None,
                 person=None):
        self.text = text
        self.content = content
        self.file = file
        self.channel_id = channel_id
        self.person = person

    def __str__(self):
        """
        Returns a human-readable string representation of this object.
        """
        return u"text={}, content={}, file={}, channel_id={}, person={}".format(
            self.text, self.content, self.file, self.channel_id, self.person)


class Speaker(Process):
    """
    Sends updates to a business messaging space
    """

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, engine=None):
        """
        Sends updates to a business messaging space

        :param engine: the overarching engine
        :type engine: Engine

        """
        Process.__init__(self)
        self.engine = engine

    def run(self):
        """
        Continuously send updates

        This function is looping on items received from the queue, and
        is handling them one by one in the background.

        Processing should be handled in a separate background process, like
        in the following example::

            speaker = Speaker(engine=my_engine)
            process_handle = speaker.start()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Alternatively, the loop is also broken when an exception is pushed
        to the queue. For example::

            engine.mouth.put(None)

        Note that items are not picked up from the queue until the underlying
        space is ready for handling messages.
        """
        logging.info(u"Starting speaker")

        try:
            self.engine.set('speaker.counter', 0)
            while self.engine.get('general.switch', 'on') == 'on':

                if self.engine.mouth.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.engine.mouth.get(True, 0.1)
                    if item is None:
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

        logging.info(u"Speaker has been stopped")

    def process(self, item):
        """
        Sends one update to a business messaging space

        :param item: the update to be transmitted
        :type item: str or object

        """

        counter = self.engine.context.increment('speaker.counter')
        logging.debug(u'Speaker is working on {}'.format(counter))

        if self.engine.space is not None:
            if isinstance(item, string_types):
                self.engine.space.post_message(id='*default', text=item)
            else:
                self.engine.space.post_message(id=item.channel_id,
                                               text=item.text,
                                               content=item.content,
                                               file=item.file,
                                               person=item.person)
        else:
            logging.info(item)
