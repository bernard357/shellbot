#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Upload


class MyChannel(object):
    is_direct = False


class MyBot(object):
    channel = MyChannel()

    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))


class UploadTests(unittest.TestCase):

    def setUp(self):
        self.engine = Engine(mouth=Queue())
        self.engine.configure()
        self.engine.shell = Shell(engine=self.engine)
        self.bot = MyBot(engine=self.engine)

    def tearDown(self):
        del self.bot
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))


    def test_init(self):

        logging.info('***** init')

        c = Upload(self.engine)

        self.assertEqual(c.keyword, u'*upload')
        self.assertEqual(c.information_message, u'Handle file upload')
        self.assertEqual(c.usage_message, None)
        self.assertTrue(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        c = Upload(self.engine)

        c.execute(self.bot, url='http://from/here', attachment='picture.png')
        self.assertEqual(
            self.engine.mouth.get().text,
            u'Thank you for the information shared!')
        with self.assertRaises(Exception):
            print(self.engine.mouth.get_nowait())


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
