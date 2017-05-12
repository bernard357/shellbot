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
from shellbot.updaters import SpaceUpdater


class UpdaterTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SpaceUpdater(bot='b', space=space, speaker=speaker)
        self.assertEqual(u.bot, 'b')

    def test_put(self):

        logging.info('***** put')

        space = mock.Mock()
        speaker = mock.Mock()
        u = SpaceUpdater(bot='b', space=space, speaker=speaker)
        item = {
            'personEmail': 'alice@acme.com',
            'text': 'my message',
        }

        u.put(item)
        self.assertEqual(u.mouth.get(), 'alice@acme.com: my message')
        with self.assertRaises(Exception):
            u.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
