#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, Speaker


class SpeakerTests(unittest.TestCase):

    def test_static(self):

        logging.info('*** Static test ***')

        bot = ShellBot(mouth=Queue())
        speaker = Speaker(bot=bot)

        speaker_process = Process(target=speaker.work)
        speaker_process.daemon = True
        speaker_process.start()

        speaker_process.join(0.1)
        if speaker_process.is_alive():
            logging.info('Stopping speaker')
            bot.context.set('general.switch', 'off')
            speaker_process.join()

        self.assertFalse(speaker_process.is_alive())
        self.assertEqual(bot.context.get('speaker.counter', 0), 0)

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        bot = ShellBot(mouth=Queue())
        bot.space.id = '123'

        items = ['hello', 'world']
        for item in items:
            bot.mouth.put(item)
        bot.mouth.put(Exception('EOQ'))

        tee = Queue()
        speaker = Speaker(bot=bot, tee=tee)

        with mock.patch.object(bot.space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.work()
            mocked.assert_any_call('hello')
            mocked.assert_called_with('world')

            with self.assertRaises(Exception):
                mouth.get_nowait()

        for item in items:
            self.assertEqual(tee.get(), item)

    def test_process(self):

        logging.info('*** Processing test ***')

        bot = ShellBot()
        bot.space.id = '123'

        speaker = Speaker(bot=bot)

        with mock.patch.object(bot.space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.process('hello world', 1)
            mocked.assert_called_with('hello world')

            class WithMarkdown(object):
                message = ''
                markdown = 'me **too**'
                file = None

            item = WithMarkdown()
            speaker.process(item, 2)
            mocked.assert_called_with('',
                                      markdown='me **too**',
                                      file_path=None)

            class WithFile(object):
                message = '*with*attachment'
                markdown = None
                file = 'http://a.server/with/file'

            item = WithFile()
            speaker.process(item, 3)
            mocked.assert_called_with('*with*attachment',
                                      markdown=None,
                                      file_path='http://a.server/with/file')

            class WithAll(object):
                message = 'hello world'
                markdown = 'hello **world**'
                file = 'http://a.server/with/file'

            item = WithAll()
            speaker.process(item, 4)
            mocked.assert_called_with('hello world',
                                      markdown='hello **world**',
                                      file_path='http://a.server/with/file')

if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
