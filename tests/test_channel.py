#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import json
import logging
from multiprocessing import Queue
import os
import sys
import yaml

from shellbot import Context
from shellbot.channel import Channel


class ChannelTests(unittest.TestCase):

    def test_init(self):

        channel = Channel()
        self.assertEqual(channel.attributes, {})

        channel = Channel(None)
        self.assertEqual(channel.attributes, {})

        channel = Channel('')
        self.assertEqual(channel.attributes, {})

        channel = Channel(attributes=None)
        self.assertEqual(channel.attributes, {})

        channel = Channel(attributes='')
        self.assertEqual(channel.attributes, {})

        data = {u'hellô': 'b', u'wörld': 123}
        channel = Channel(attributes=json.dumps(data))
        self.assertEqual(channel.attributes, data)

        data = {u'hellô': 'b', u'wörld': 123}
        channel = Channel(attributes=data)
        self.assertEqual(channel.attributes, data)

        data = {
              "id" : "Z2lzY29zcGFyazovL3VzDNiZC01YjNkZmM1NjVk",
              "title" : "A fancy channel",
              "is_direct" : True,
              "is_moderated" : False,
            }

        channel = Channel(data)
        self.assertEqual(channel.id, "Z2lzY29zcGFyazovL3VzDNiZC01YjNkZmM1NjVk")
        self.assertEqual(channel.title, "A fancy channel")
        self.assertTrue(channel.is_direct)
        self.assertFalse(channel.is_moderated)

    def test___getattr__(self):

        channel = Channel()
        with self.assertRaises(AttributeError):
            value = channel.unknown

        data = {u'hello': u'wörld', 'number': 123, 'weird': None}

        channel = Channel(attributes=data)
        self.assertEqual(channel.hello, u'wörld')
        self.assertEqual(channel.number, 123)
        self.assertEqual(channel.weird, None)

        channel = Channel(attributes=json.dumps(data))
        self.assertEqual(channel.hello, u'wörld')
        self.assertEqual(channel.number, 123)
        self.assertEqual(channel.weird, None)

    def test_get(self):

        channel = Channel()
        with self.assertRaises(AttributeError):
            value = channel.unknown
        self.assertEqual(channel.get('unknown'), None)
        self.assertEqual(channel.get('unknown', 'hye'), 'hye')

        data = {u'hellô': u'wörld', 'number': 123, 'weird': None}

        channel = Channel(attributes=data)
        self.assertEqual(channel.get(u'hellô'), u'wörld')
        self.assertEqual(channel.get('number'), 123)
        self.assertEqual(channel.get('weird'), None)
        self.assertEqual(channel.get('weird', []), [])

        channel = Channel(attributes=json.dumps(data))
        self.assertEqual(channel.get(u'hellô'), u'wörld')
        self.assertEqual(channel.get('number'), 123)
        self.assertEqual(channel.get('weird'), None)
        self.assertEqual(channel.get('weird', []), [])

    def test___setattr__(self):

        data = {'personEmail': 'foo@acme.com'}
        channel = Channel(attributes=data)

        with self.assertRaises(AttributeError):
            value = channel.person_name

        channel.person_name = channel.personEmail
        self.assertEqual(channel.person_name, 'foo@acme.com')

    def test___repr__(self):

        channel = Channel()
        self.assertEqual(repr(channel), 'Channel({})')

    def test___str__(self):

        channel = Channel()
        self.assertEqual(str(channel), '{}')

        data = {u'hellô': u'wörld', 'number': 123}
        channel = Channel(attributes=json.dumps(data))
        self.assertEqual(json.loads(str(channel)), data)
        self.assertEqual(yaml.safe_load(str(channel)), data)

    def test___eq__(self):

        a = Channel({"hello": "world"})
        b = Channel({"hello": "world"})
        self.assertEqual(a, b)

        a = Channel({"hello": "world"})
        b = Channel({"hello": "world"})
        self.assertTrue(a.__eq__(b))
        self.assertTrue(b.__eq__(a))

        a = Channel({"hello": "world"})
        b = Channel({"hello": "moon"})
        self.assertFalse(a.__eq__(b))
        self.assertFalse(b.__eq__(a))

        a = Channel({"hello": "world"})
        b = {"hello": "world"}
        self.assertFalse(a.__eq__(b))


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
