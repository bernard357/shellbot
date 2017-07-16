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

from bottle import request
import logging
from multiprocessing import Process, Queue, Manager
import os
import signal
from six import string_types
import time


class Space(object):
    """
    Handles a collaborative space

    The life cycle of a space can be described as follows::

    1. A space instance is created and configured::

           >>>my_context = Context(...)
           >>>space = Space(context=my_context)

    2. The space is connected to some back-end API::

           >>>space.connect()

    3. The space is shadowed in the cloud::

           >>>space.bond()
           >>>space.is_ready
           True

       In some cases, the space can be disposed first, and recreated later on::

           >>>space.dispose()
           >>>space.is_ready
           False

           ...

           >>>space.bond()
           >>>space.is_ready
           True

    4. Messages can be posted::

           >>>space.post_message('Hello, World!')

    5. When the space is coming end of life, all resources can be disposed::

           >>space.dispose()


    Multiple modes can be considered for the handling of inbound
    events from the cloud.

    - Asynchronous reception - the back-end API sends updates over a web hook
      to this object, and messages are pushed to the listening queue.

      Example::

            # link local web server to this space
            server.add_route('/hook', space.webhook)

            # link cloud service to this local server
            space.register('http://my.server/hook')

    - Background loop - this object pulls the API in a loop, and new messages
      are pushed to the listening queue.

      Example::

            space.run()
    """

    DEFAULT_SETTINGS = {

        'space': {
            'room': '$CHAT_ROOM_TITLE',
            'moderators': '$CHAT_ROOM_MODERATORS',
        },

        'server': {
            'url': '$SERVER_URL',
            'hook': '/hook',
            'binding': None,
            'port': 8080,
        },

    }

    DEFAULT_SPACE_TITLE = u'Collaboration space'

    PULL_INTERVAL = 0.05  # time between pulls, when not hooked

    def __init__(self,
                 context=None,
                 ears=None,
                 **kwargs):
        """
        Handles a collaborative space

        :param context: the overarching context
        :type context: Context

        :param ears: the listening queue
        :type ears: Queue

        Example::

            space = Space(context=my_engine.context,
                          ears=my_engine.ears)

        """
        # prevent Manager() process to be interrupted
        handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.values = Manager().dict()

        # restore current handler for the rest of the program
        signal.signal(signal.SIGINT, handler)

        self.context = context
        self.ears = ears

        self.on_init(**kwargs)

        self.reset()

    def on_init(self, prefix='space', **kwargs):
        """
        Handles extended initialisation parameters

        :param prefix: the main keyword for configuration of this space
        :type prefix: str

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_init(self, prefix='secondary.space', **kwargs):
                ...

        """
        assert prefix not in (None, '')
        self.prefix = prefix

    def get(self, key, default=None):
        """
        Retrieves the value of one configuration key

        :param key: name of the value
        :type key: str

        :param default: default value
        :type default: any serializable type is accepted

        :return: the actual value, or the default value, or None

        This function is a proxy for underlying context. It combines
        the configuration prefix for this instance with the provided key
        before lookup. Typically, if the prefix is ``special_space`` and the
        function is called with key ``id``, then the function actually looks
        for the attribute ``special_space.id``.

        Example::

            configured_title = space.get('title')

        This function is safe on multiprocessing and multithreading.

        """
        try:
            return self.context.get(self.prefix+'.'+key, default)
        except AttributeError:
            return default

    def set(self, key, value):
        """
        Changes the value of one configuration key

        :param key: name of the value
        :type key: str

        :param value: new value
        :type value: any serializable type is accepted

        This function is a proxy for underlying context. It combines
        the configuration prefix for this instance with the provided key
        before change. Typically, if the prefix is ``special_space`` and the
        function is called with key ``title``, then the function actually sets
        the attribute ``special_space.title``.

        Example::

            space.set('some_key', 'some_value')
            ...
            value = space.get('some_key')  # 'some_value'

        This function is safe on multiprocessing and multithreading.

        """
        self.context.set(self.prefix+'.'+key, value)

    def reset(self):
        """
        Resets a space

        After a call to this function, ``bond()`` has to be invoked to
        return to normal mode of operation.
        """
        self.values.clear()

        self.on_reset()

    def on_reset(self):
        """
        Adds processing to space reset

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_reset(self):
                self._last_message_id = 0

        """
        pass

    def configure(self, settings={}):
        """
        Changes settings of the space

        :param settings: a dictionary with some statements for this instance
        :type settings: dict

        After a call to this function, ``bond()`` has to be invoked to
        return to normal mode of operation.
        """
        self.context.apply(settings)
        self.check()
        self.reset()

    def check(self):
        """
        Checks settings

        This function should be expanded in sub-class, where necessary.

        Example::

            def check(self):
                self.engine.context.check(self.prefix+'.title',
                                          is_mandatory=True)

        """
        pass

    def configured_title(self):
        """
        Returns the title of the space as set in configuration

        :return: the configured title, or ``Collaboration space``
        :rtype: str

        This function should be rewritten in sub-classes if
        space title does not come from ``space.title`` parameter.
        """
        return self.get('title', self.DEFAULT_SPACE_TITLE)

    def connect(self, **kwargs):
        """
        Connects to the back-end API

        This function should be expanded in sub-class, where necessary.

        Example::

            def connect(self, **kwargs):
                self.api = ApiFactory(self.token)

        """
        pass

    def bond(self,
             title=None,
             moderators=None,
             participants=None,
             **kwargs):
        """
        Creates or binds to a named space

        :param title: the title of the target space (optional)
        :type title: str

        :param moderators: the list of initial moderators (optional)
        :type moderators: list of str

        :param participants: the list of initial participants (optional)
        :type participants: list of str

        Example::

            space = Space(...)
            space.connect()
            space.bond()

        This function either bonds to an existing space, or creates a new space
        if necessary. In later case it also adds moderators and participants.

        """
        if title in (None, ''):
            title = self.configured_title()

        assert title not in (None, '')

        if not self.lookup_space(title=title, **kwargs):

            self.create_space(title=title, **kwargs)

            if moderators is None:
                moderators = self.get('moderators', [])
            self.add_moderators(moderators)

            if participants is None:
                participants = self.get('participants', [])
            self.add_participants(participants)

        self.on_bond()

    def on_bond(self):
        """
        Adds processing to space bond

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_bond(self):
                self.post_message('I am alive!')

        """
        pass

    @property
    def is_ready(self):
        """
        Checks if this space is ready for interactions

        :return: True or False
        """
        if self.id is None:
            return False

        return True

    @property
    def id(self):
        """
        Retrieves id of this space
        """
        return self.values.get('id')

    @property
    def title(self):
        """
        Retrieves title of this space
        """
        return self.values.get('title')

    def use_space(self, id, **kwargs):
        """
        Uses an existing space

        :param id: id of the target space
        :type id: str

        :return: True on success, False otherwise

        If a space already exists with this id, this object is
        configured to use it and the function returns True.

        Else the function returns False.

        This function should be implemented in sub-class.

        Example::

            def use_space(self, id, **kwargs):
                return self.api.rooms.lookup(id=id)

        """
        return False

    def lookup_space(self, title=None, **kwargs):
        """
        Looks for an existing space by name

        :param title: title of the target space
        :type title: str

        :return: True on successful lookup, False otherwise

        If a space already exists with this title, this object is
        configured to use it and the function returns True.

        Else the function returns False.

        This function should be implemented in sub-class.

        Example::

            def lookup_space(self, title, **kwargs):
                return self.api.rooms.lookup(title=title)

        """
        return False

    def create_space(self, title, **kwargs):
        """
        Creates a space

        :param title: title of the target space
        :type title: str

        On successful space creation, this object should be configured
        to use it.

        This function should be implemented in sub-class.

        Example::

            def create_space(self, title=None, **kwargs):
                self.api.rooms.create(title=title)

        """
        raise NotImplementedError()

    def add_moderators(self, persons=[]):
        """
        Adds multiple moderators

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info(u"Adding moderators")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.add_moderator(person)

    def add_moderator(self, person):
        """
        Adds one moderator

        :param person: e-mail address of the person to add
        :type person: str

        This function should be implemented in sub-class.

        Example::

            def add_moderator(self, person):
                self.api.memberships.create(id=self.id,
                                            person=person,
                                            is_moderator=True)

        """
        raise NotImplementedError()

    def add_participants(self, persons=[]):
        """
        Adds multiple participants

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info(u"Adding participants")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.add_participant(person)

    def add_participant(self, person):
        """
        Adds one participant

        :param person: e-mail address of the person to add
        :type person: str

        This function should be implemented in sub-class.

        Example::

            def add_participant(self, person):
                self.api.memberships.create(id=self.id, person=person)

        """
        raise NotImplementedError()

    def remove_participants(self, persons=[]):
        """
        Removes multiple participants

        :param persons: e-mail addresses of persons to delete
        :type persons: list of str

        """
        logging.info(u"Removing participants")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.remove_participant(person)

    def remove_participant(self, person):
        """
        Removes one participant

        :param person: e-mail address of the person to delete
        :type person: str

        This function should be implemented in sub-class.

        Example::

            def remove_participant(self, person):
                self.api.memberships.delete(id=self.id, person=person)

        """
        raise NotImplementedError()

    def dispose(self, **kwargs):
        """
        Disposes all resources

        This function deletes the underlying space in the cloud and reset
        this instance. It is useful to restart a clean environment.

        >>>space.bond(title="Working Space")
        ...
        >>>space.dispose()

        After a call to this function, ``bond()`` has to be invoked to
        return to normal mode of operation.
        """

        if self.title in (None, '', self.DEFAULT_SPACE_TITLE):
            title = self.configured_title()
        else:
            title = self.values.get('title')

        self.delete_space(title=title, **kwargs)
        self.reset()

    def delete_space(self, title=None, **kwargs):
        """
        Deletes a space

        :param title: title of the space to be deleted (optional)
        :type title: str

        After a call to this function the underlying space does not appear
        anymore in the list of available resources. This can be implemented in
        the back-end either by actual deletion of resources, or by archiving
        the space. In the second scenario, the space could be restored at a
        later stage if needed.

        >>>space.delete_space("Obsolete Space")

        This function should be implemented in sub-class.

        Example::

            def delete_space(self, title=None, **kwargs):
                self.api.rooms.delete(title=title)

        """
        raise NotImplementedError()

    def post_message(self,
                     text=None,
                     content=None,
                     file=None,
                     space_id=None,
                     **kwargs):
        """
        Posts a message

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as Markdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        :param space_id: unique id of the target space
        :type space_id: str

        Example message out of plain text::

        >>>space.post_message(text='hello world')

        If no space id is provided, then the function can use the unique id
        of this space, if one has been defined. Or an exception may be raised
        if no id has been made available.

        This function should be implemented in sub-class.

        Example::

            def post_message(self, text=None, **kwargs):
                self.api.messages.create(text=text)

        """
        raise NotImplementedError()

    def webhook(self):
        """
        Handles updates sent over the internet

        This function should use the ``request`` object to retrieve details
        of the web transaction.

        This function should be implemented in sub-class.

        Example::

            def webhook(self):

                message_id = request.json['data']['id']
                item = self.api.messages.get(messageId=message_id)
                self.ears.put(item._json)
                return "OK"

        """
        raise NotImplementedError()

    def register(self, hook_url):
        """
        Registers to the cloud API for the reception of updates

        :param hook_url: web address to be used by cloud service
        :type hook_url: str

        This function should be implemented in sub-class.

        Example::

            def register(self, hook_url):
                self.api.register(hook_url)

        """
        raise NotImplementedError()

    def start(self, hook_url=None):
        """
        Starts the update process

        :param hook_url: web address to be used by cloud service (optional)
        :type hook_url: str

        :return: either the process that has been started, or None

        If an URL is provided, it is communicated to the back-end API
        for asynchronous updates.

        Else this function starts a separate daemonic process to pull
        updates in the background.
        """

        self.on_start()

        if hook_url:
            self.register(hook_url=hook_url)

        else:
            p = Process(target=self.run)
            p.daemon = True
            p.start()
            return p

    def on_start(self):
        """
        Adds processing just before first update reception

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_start(self):
                self.find_my_bot_id()

        """
        pass

    def run(self):
        """
        Continuously fetches updates

        This function senses new items at regular intervals, and pushes them
        to the listening queue.

        Processing is handled in a separate background process, like
        in the following example::

            # gets updates in the background
            process = space.start()

            ...

            # wait for the end of the process
            process.join()

        The recommended way for stopping the process is to change the
        parameter ``general.switch`` in the context. For example::

            engine.set('general.switch', 'off')

        Note: this function should not be invoked if a webhok has been
        configured.

        """

        logging.info(u'Pulling updates')

        try:
            self.context.set('puller.counter', 0)
            while self.context.get('general.switch', 'on') == 'on':

                try:
                    self.pull()
                    self.context.increment('puller.counter')
                    time.sleep(self.PULL_INTERVAL)

                except Exception as feedback:
                    logging.exception(feedback)
                    break

        except KeyboardInterrupt:
            pass

        logging.info(u"Puller has been stopped")

    def pull(self):
        """
        Fetches updates

        This function senses most recent items, and pushes them
        to the listening queue.

        This function should be implemented in sub-class.

        Example::

            def pull(self):
                for message in self.api.list_message():
                    self.ears.put(message)

        """
        raise NotImplementedError()
