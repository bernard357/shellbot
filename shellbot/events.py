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
from six import string_types


class Event(object):
    """
    Represents an event received from the chat system

    Events, and derivated objects such as instances of Message, abstract
    pieces of information received from various chat systems. They are
    designed as dictionary wrappers, with minimum exposure to shellbot, while
    enabling the transmission of rich information through serialization.

    The life cycle of an event starts within a Space instance, most often, in
    the webhook triggered by a remote chat system. In order to adapt to
    shellbot, code should build the appropriate event instance, and push
    it to the queue used by the listener.

    Example::

        item = self.api.messages.get(messageId=message_id)
        self.bot.ears.put(Message(item._json))

    """
    type = 'event'

    def __init__(self,
                 attributes=None):
        """
        Represents an event received from the chat system

        :param attributes: the set of atributes of this event
        :type attributes: dict or json-encoded string

        This function may raise AttributeError if some manadatory
        attribute is missing.

        """
        if attributes in (None, ''):
            self.__dict__['attributes'] = {}

        elif isinstance(attributes, string_types):
            self.__dict__['attributes'] = json.loads(attributes)

        else:
            self.__dict__['attributes'] = attributes

        try:
            del self.__dict__['attributes']['type']
        except:
            pass

    def __getattr__(self, key):
        """
        Provides access to any native attribute

        :param key: name of the attribute
        :type key: str

        :return: the value of the attribute

        This method is called when attempting to access a object attribute that
        hasn't been defined for the object.  For example trying to access
        object.attribute1 when attribute1 hasn't been defined.
        Event.__getattr__() checks original attributes to see if the
        attribute exists, and returns its value. Else an
        AttributeError is raised.

        """
        try:
            return self.attributes[key]

        except KeyError:
            raise AttributeError(u"'{}' has no attribute '{}'".format(
                self.__class__.__name__, key))

    def __setattr__(self, key, value):
        """
        Changes an attribute

        :param key: name of the attribute
        :type key: str

        :param value: new value of the attribute
        :type value: str or other serializable object

        The use case for this function is when you adapt an event that does
        not feature an attribute that is expected by shellbot.

        For example, Cisco Spark messages do not feature the key ``from_name``
        but have ``personEmail`` instead. This can be adapted like this::

            message = Message(received_item)
            message.from_name = message.personEmail

        """
        self.attributes[key] = value

    def get(self, key, default=None):
        """
        Returns the value of one attribute
        :param key: name of the attribute
        :type key: str

        :param default: default value of the attribute
        :type default: str or other serializable object

        :return: value of the attribute
        :rtype: str or other serializable object or None

        The use case for this function is when you adapt an event that does
        not feature an attribute that is expected by shellbot.
        More specifically, call this function on optional attributes so as
        to avoid AttributeError

        For example, some Cisco Spark messages may have ``toPersonId``, but
        not all. So you could do::

            message = Message(received_item)
            to_id = message.get('toPersonId')
            if to_id:
               ...

        """
        value = self.attributes.get(key) # do not use default here!
        if value is None:
            value = default
        return value

    def __repr__(self):
        """
        Returns a string representing this object as valid Python expression.
        """
        return "{}({})".format(
            self.__class__.__name__,
            json.dumps(self.attributes, sort_keys=True))

    def __str__(self):
        """
        Returns a human-readable string representation of this object.
        """
        with_type = self.attributes.copy()
        with_type.update({'type': self.type})
        return json.dumps(with_type, sort_keys=True)

    def __eq__(self, other):
        """
        Compares with another object
        """
        try:
            if self.type != other.type:
                return False

            if self.attributes != other.attributes:
                return False

            return True

        except:
            return False  # not same duck types


class Message(Event):
    """
    Represents a message received from the chat system
    """

    type = 'message'

    @property
    def text(self):
        """
        Returns message textual content

        :rtype: str

        This function returns a bare string that can be handled
        directly by the shell. This has no tags nor specific binary format.
        """
        return self.__getattr__('text')

    @property
    def content(self):
        """
        Returns message rich content

        :rtype: str

        This function preserves rich content that was used to create the
        message, be it Markdown, HTML, or something else.

        If no rich content is provided, than this attribute is equivalent
        to ``self.text``

        """
        content = self.attributes.get('content')
        if content not in (None, ''):
            return content

        return self.__getattr__('text')

    @property
    def from_id(self):
        """
        Returns the id of the message originator

        :rtype: str or None

        This attribute allows listener to distinguish between messages
        from the bot and messages from other chat participants.
        """
        return self.attributes.get('from_id')

    @property
    def from_label(self):
        """
        Returns the name or title of the message originator

        :rtype: str or None

        This attribute is used by updaters that log messages or copy them
        for archiving.
        """
        return self.attributes.get('from_label')

    @property
    def mentioned_ids(self):
        """
        Returns the list of mentioned persons

        :rtype: list of str, or []

        This attribute allows the listener to determine if the input is
        explicitly for this bot or not.
        """
        return self.attributes.get('mentioned_ids', [])

    @property
    def space_id(self):
        """
        Returns the id of the chat space

        :rtype: str or None

        """
        return self.attributes.get('space_id')


class Attachment(Event):
    """
    Represents the attachment of a file to a space
    """

    type = 'attachment'

    @property
    def url(self):
        """
        Returns link to file content

        :rtype: str
        """
        return self.__getattr__('url')

    @property
    def from_id(self):
        """
        Returns the id of the message originator

        :rtype: str or None

        This attribute allows listener to distinguish between messages
        from the bot and messages from other chat participants.
        """
        return self.attributes.get('from_id')

    @property
    def from_label(self):
        """
        Returns the name or title of the message originator

        :rtype: str or None

        This attribute is used by updaters that log messages or copy them
        for archiving.
        """
        return self.attributes.get('from_label')

    @property
    def space_id(self):
        """
        Returns the id of the chat space

        :rtype: str or None

        """
        return self.attributes.get('space_id')


class Join(Event):
    """
    Represents the addition of someone to a space
    """

    type = 'join'

    @property
    def actor_id(self):
        """
        Returns the id of the joining actor

        :rtype: str or None

        This attribute allows listener to identify who joins a space.
        """
        return self.__getattr__('actor_id')

    @property
    def actor_label(self):
        """
        Returns the name or title of the joining actor

        :rtype: str or None

        This attribute allows listener to identify who joins a space.
        """
        return self.__getattr__('actor_label')

    @property
    def space_id(self):
        """
        Returns the id of the joined space

        :rtype: str or None

        """
        return self.__getattr__('space_id')


class Leave(Event):
    """
    Represents the removal of someone to a space
    """

    type = 'leave'

    @property
    def actor_id(self):
        """
        Returns the id of the leaving actor

        :rtype: str or None

        This attribute allows listener to identify who leaves a space.
        """
        return self.__getattr__('actor_id')

    @property
    def actor_label(self):
        """
        Returns the name or title of the leaving actor

        :rtype: str or None

        This attribute allows listener to identify who leaves a space.
        """
        return self.__getattr__('actor_label')

    @property
    def space_id(self):
        """
        Returns the id of the left space

        :rtype: str or None

        """
        return self.__getattr__('space_id')

