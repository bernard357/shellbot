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
from shellbot.events import Message
from shellbot.updaters import FileUpdater

my_bot = ShellBot()
my_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/local'
my_file = my_path + '/file_updater.log'


class UpdaterTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        u = FileUpdater()
        self.assertEqual(u.bot, None)

        u = FileUpdater(bot=my_bot)
        self.assertEqual(u.bot, my_bot)

    def test_on_init(self):

        logging.info('***** on_init')

        u = FileUpdater()
        self.assertEqual(u.path, None)

        u = FileUpdater(path=None)
        self.assertEqual(u.path, None)

        u = FileUpdater(path='')
        self.assertEqual(u.path, '')

        u = FileUpdater(path='here.log')
        self.assertEqual(u.path, 'here.log')

    def test_get_path(self):

        logging.info('***** get_path')

        u = FileUpdater(bot=my_bot)
        self.assertEqual(u.get_path(), '/var/log/shellbot.log')

        u = FileUpdater(bot=my_bot, path=None)
        self.assertEqual(u.get_path(), '/var/log/shellbot.log')

        u = FileUpdater(bot=my_bot, path='')
        self.assertEqual(u.get_path(), '/var/log/shellbot.log')

        u = FileUpdater(bot=my_bot, path='here.log')
        self.assertEqual(u.get_path(), 'here.log')

    def test_on_bond(self):

        logging.info('***** on_bond')

        try:
            os.rmdir(my_path+'/on_bond')
        except:
            pass

        u = FileUpdater(path=my_path+'/on_bond/file.log')
        u.on_bond()
        self.assertTrue(os.path.isdir(my_path+'/on_bond'))

        try:
            os.rmdir(my_path+'/on_bond')
        except:
            pass

    def test_put(self):

        logging.info('***** put')

        try:
            os.remove(my_file)
        except:
            pass

        try:
            os.rmdir(my_path)
        except:
            pass

        u = FileUpdater(path=my_file)
        u.on_bond()

        message_1 = Message({
            'person_label': 'alice@acme.com',
            'text': 'a first message',
        })
        u.put(message_1)

        message_2 = Message({
            'person_label': 'bob@acme.com',
            'text': 'a second message',
        })
        u.put(message_2)

        expected = '{"person_label": "alice@acme.com", "text": "a first message", "type": "message"}\n{"person_label": "bob@acme.com", "text": "a second message", "type": "message"}\n'
        with open(my_file, 'r') as handle:
            self.assertEqual(handle.read(), expected)

        try:
            os.remove(my_file)
        except:
            pass

        try:
            os.rmdir(my_path)
        except:
            pass


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
