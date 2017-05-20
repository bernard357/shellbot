#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, ShellBot, Shell
from shellbot.events import Event, Message, Attachment, Join, Leave
from shellbot.updaters import SparkSpaceUpdater


class UpdaterTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SparkSpaceUpdater(bot='b', space=space, speaker=speaker)
        self.assertEqual(u.bot, 'b')

    def test_put(self):

        logging.info('***** put')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SparkSpaceUpdater(bot='b', space=space, speaker=speaker)
        item = Message({
            'from_label': 'alice@acme.com',
            'text': 'my message',
        })

        u.put(item)
        self.assertEqual(u.mouth.get(), 'alice@acme.com: my message')
        with self.assertRaises(Exception):
            u.mouth.get_nowait()

    def test_format(self):

        logging.info('***** format')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SparkSpaceUpdater(bot='b', space=space, speaker=speaker)

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
