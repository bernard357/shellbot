#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

from shellbot import Context, Engine, Shell, Vibes
from shellbot.commands import Close

my_engine = Engine(mouth=Queue())
my_engine.shell = Shell(engine=my_engine)


class Bot(object):
    def __init__(self, engine):
        self.engine = engine

    def say(self, text, content=None, file=None):
        self.engine.mouth.put(Vibes(text, content, file))

    def dispose(self):
        pass


my_bot = Bot(engine=my_engine)


class CloseTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        c = Close(my_engine)

        self.assertEqual(c.keyword, u'close')
        self.assertEqual(c.information_message, u'Close this space')
        self.assertEqual(c.usage_message, None)
        self.assertFalse(c.is_hidden)

    def test_execute(self):

        logging.info('***** execute')

        my_engine.stop = mock.Mock()
        my_engine.dispose = mock.Mock()

        c = Close(my_engine)

        with mock.patch.object(my_bot,
                               'dispose',
                               return_value=None) as mocked:
            c.execute(my_bot)
            self.assertTrue(my_bot.dispose.called)

        self.assertEqual(my_engine.mouth.get().text, u'Closing this channel')
        with self.assertRaises(Exception):
            my_engine.mouth.get_nowait()



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
