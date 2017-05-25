#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.events import Event, Message, Attachment, Join, Leave
from shellbot.updaters import SpaceUpdater


class UpdaterTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SpaceUpdater(space=space, speaker=speaker)
        self.assertEqual(u.bot, None)

    def test_put(self):

        logging.info('***** put')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SpaceUpdater(space=space, speaker=speaker)

        item = Message({
            'from_label': 'alice@acme.com',
            'text': 'my message',
        })

        u.put(item)
        self.assertEqual(u.mouth.get(), 'alice@acme.com: my message')
        with self.assertRaises(Exception):
            u.mouth.get_nowait()

        item = Attachment({
            'from_label': 'alice@acme.com',
            'text': 'my message',
            'url': 'http://some.server/some/file',
        })

        class FakeSpace(object):
            def download_attachment(self, url):
                return 'some_file.pdf'

        u.space = FakeSpace()
        u.put(item)
        self.assertEqual(u.mouth.get().text, u'alice@acme.com: some_file.pdf')
        with self.assertRaises(Exception):
            u.mouth.get_nowait()

    def test_format(self):

        logging.info('***** format')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SpaceUpdater(space=space, speaker=speaker)

        inbound = Event({
            'who_cares': 'no attribute will be used anayway',
        })
        outbound = u.format(inbound)
        self.assertEqual(outbound, u'an unknown event has been received')

        inbound = Message({
            'from_label': 'alice@acme.com',
            'text': 'my message',
        })
        outbound = u.format(inbound)
        self.assertEqual(outbound, 'alice@acme.com: my message')

        inbound = Message({
            'from_label': 'alice@acme.com',
            'text': 'my message',
            'content': '<p>my message</p>',
        })
        outbound = u.format(inbound)
        self.assertEqual(outbound.text, 'alice@acme.com: my message')
        self.assertEqual(outbound.content, 'alice@acme.com: <p>my message</p>')

        inbound = Attachment({
            'url': 'http://my.server/my/file',
        })
        outbound = u.format(inbound)
        self.assertEqual(outbound, u'http://my.server/my/file has been shared')

        inbound = Join({
            'actor_label': 'alice@acme.com',
        })
        outbound = u.format(inbound)
        self.assertEqual(outbound, u'alice@acme.com has joined')

        inbound = Leave({
            'actor_label': 'alice@acme.com',
        })
        outbound = u.format(inbound)
        self.assertEqual(outbound, u'alice@acme.com has left')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
