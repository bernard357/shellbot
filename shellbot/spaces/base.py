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
from multiprocessing import Process, Queue
import os
from six import string_types
import time


class Space(object):
    """
    Handles a collaborative space

    A collaborative space supports multiple channels for interactions between
    persons and bots.

    The life cycle of a space can be described as follows::

    1. A space instance is created and configured::

            >>>my_context = Context(...)
            >>>space = Space(context=my_context)

    2. The space is connected to some back-end API::

            >>>space.connect()

    3. Multiple channels can be handled by a single space::

            channel = space.create(title)

            channel = space.get_by_title(title)
            channel = space.get_by_id(id)

            channel.title = 'A new title'
            space.update(channel)

            space.delete(id)

       Channels feature common attributes, yet can be extended to
       convey specificities of some platforms.

    4. Messages can be posted::

           >>>space.post_message(id, 'Hello, World!')

    5. The interface distinguishes between space participants and
       moderators::

            space.add_participants(id, persons)
            space.add_participant(id, person)
            space.add_moderators(id, persons)
            space.add_moderator(id, person)
            space.remove_participants(id, persons)
            space.remove_participant(id, person)


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
            'title': '$CHAT_ROOM_TITLE',
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
        self.context = context
        self.ears = ears

        self.on_init(**kwargs)

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

    def on_start(self):
        """
        Reacts when engine is started

        This function should be expanded in sub-class, where necessary.

        Example::

            def on_start(self):
                self.load_cache_from_db()

        """
        pass

    def on_stop(self):
        """
        reacts when engine is stopped

        This function attempts to deregister webhooks, if any. This behaviour
        can be expanded in sub-class, where necessary.

        """
        self.deregister()

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

        This function should be expanded in sub-class, where required.

        Example::

            def connect(self, **kwargs):
                self.api = ApiFactory(self.token)

        """
        pass

    def create(self, title, **kwargs):
        """
        Creates a channel

        :param title: title of the new channel
        :type title: str

        :return: Channel

        This function returns a representation of the new channel on success,
        else it should raise an exception.

        This function should be implemented in sub-class.

        Example::

            def create(self, title=None, **kwargs):
                handle = self.api.rooms.create(title=title)
                return Channel(handle.attributes)

        """
        raise NotImplementedError()

    def get_by_title(self, title=None, **kwargs):
        """
        Looks for an existing space by title

        :param title: title of the target channel
        :type title: str

        :return: Channel instance or None

        If a channel already exists with this id, a representation of it is
        returned. Else the value ``None``is returned.

        This function should be implemented in sub-class.

        Example::

            def get_by_title(self, title, **kwargs):
                for handle in self.api.rooms.list()
                if handle.title == title:
                    return Channel(handle.attributes)

        """
        assert title not in (None, '')
        return None

    def get_by_id(self, id, **kwargs):
        """
        Looks for an existing channel by id

        :param id: id of the target channel
        :type id: str

        :return: Channel instance or None

        If a channel already exists with this id, a representation of it is
        returned. Else the value ``None``is returned.

        This function should be implemented in sub-class.

        Example::

            def get_by_id(self, id, **kwargs):
                handle = self.api.rooms.lookup(id=id)
                if handle:
                    return Channel(handle.attributes)

        """
        assert id not in (None, '')
        return None

    def get_by_person(self, label, **kwargs):
        """
        Looks for an existing private channel with a person

        :param label: the display name of the person's account
        :type label: str

        :return: Channel instance or None

        If a channel already exists for this person, a representation of it is
        returned. Else the value ``None``is returned.

        This function should be implemented in sub-class.

        Example::

            def get_by_id(self, id, **kwargs):
                handle = self.api.rooms.lookup(id=id)
                if handle:
                    return Channel(handle.attributes)

        """
        assert label not in (None, '')
        return None

    def update(self, channel, **kwargs):
        """
        Updates an existing channel

        :param channel: a representation of the updated channel
        :type channel: Channel

        This function should raise an exception when the update is not
        successful.

        This function should be implemented in sub-class.

        Example::

            def update(self, channel):
                self.api.rooms.update(channel.attributes)

        """
        raise NotImplementedError

    def delete(self, id, **kwargs):
        """
        Deletes a channel

        :param id: the unique id of an existing channel
        :type id: str

        After a call to this function the related channel does not appear
        anymore in the list of available resources in the chat space.
        This can be implemented in the back-end either by actual deletion of
        resources, or by archiving the channel. In the second scenario, the
        channel could be restored at a later stage if needed.

        This function should be implemented in sub-class.

        Example::

            def delete(self, id=id, **kwargs):
                self.api.rooms.delete(id)

        """
        raise NotImplementedError()

    def add_moderators(self, id, persons=[]):
        """
        Adds multiple moderators

        :param id: the unique id of an existing channel
        :type id: str

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info(u"Adding moderators")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.add_moderator(id=id, person=person)

    def add_moderator(self, id, person):
        """
        Adds one moderator

        :param id: the unique id of an existing channel
        :type id: str

        :param person: e-mail address of the person to add
        :type person: str

        This function should be implemented in sub-class.

        Example::

            def add_moderator(self, id, person):
                self.api.memberships.create(id=id,
                                            person=person,
                                            is_moderator=True)

        """
        raise NotImplementedError()

    def add_participants(self, id, persons=[]):
        """
        Adds multiple participants

        :param id: the unique id of an existing channel
        :type id: str

        :param persons: e-mail addresses of persons to add
        :type persons: list of str

        """
        logging.info(u"Adding participants")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.add_participant(id=id, person=person)

    def add_participant(self, id, person):
        """
        Adds one participant

        :param id: the unique id of an existing channel
        :type id: str

        :param person: e-mail address of the person to add
        :type person: str

        This function should be implemented in sub-class.

        Example::

            def add_participant(self, id, person):
                self.api.memberships.create(id=id, person=person)

        """
        raise NotImplementedError()

    def remove_participants(self, id, persons=[]):
        """
        Removes multiple participants

        :param id: the unique id of an existing channel
        :type id: str

        :param persons: e-mail addresses of persons to delete
        :type persons: list of str

        """
        logging.info(u"Removing participants")
        for person in persons:
            logging.info(u"- {}".format(person))
            self.remove_participant(id=id, person=person)

    def remove_participant(self, id, person):
        """
        Removes one participant

        :param id: the unique id of an existing channel
        :type id: str

        :param person: e-mail address of the person to delete
        :type person: str

        This function should be implemented in sub-class.

        Example::

            def remove_participant(self, id, person):
                self.api.memberships.delete(id=id, person=person)

        """
        raise NotImplementedError()

    def post_message(self,
                     id=None,
                     text=None,
                     content=None,
                     file=None,
                     person=None,
                     **kwargs):
        """
        Posts a message

        :param id: the unique id of an existing channel
        :type id: str

        :param person: address for a direct message
        :type person: str

        :param text: message in plain text
        :type text: str

        :param content: rich format, such as Markdown or HTML
        :type content: str

        :param file: URL or local path for an attachment
        :type file: str

        Example message out of plain text::

           space.post_message(id=id, text='hello world')

        Example message with Markdown::

           space.post_message(id, content='this is a **bold** statement')

        Example file upload::

           space.post_message(id, file='./my_file.pdf')

        Of course, you can combine text with the upload of a file::

           text = 'This is the presentation that was used for our meeting'
           space.post_message(id=id,
                              text=text,
                              file='./my_file.pdf')

        For direct messages, provide who you want to reach instead of
        a channel id, like this::

            space.post_message(person='foo.bar@acme.com', text='hello guy')

        This function should be implemented in sub-class.

        Example::

            def post_message(self, id, text=None, **kwargs):
                self.api.messages.create(id=id, text=text)

        """
        assert id or person  # need a recipient
        assert id is None or person is None  # only one recipient
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

    def deregister(self):
        """
        Stops updates from the cloud back-end

        This function should be implemented in sub-class.

        """
        pass

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
