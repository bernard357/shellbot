#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Version

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


my_bot = Bot(engine=my_engine)


class VersionTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Version(my_engine)

        self.assertEqual(c.keyword, u'version')
        self.assertEqual(c.information_message, u'Display software version')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        my_engine.shell.configure(settings={
            'bot': {'name': 'testy', 'version': '17.4.1'},
        })

        c = Version(my_engine)

        c.execute(my_bot)
        self.assertEqual(my_engine.mouth.get().text, 'testy version 17.4.1')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
