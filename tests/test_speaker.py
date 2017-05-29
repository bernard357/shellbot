#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
from multiprocessing import Process, Queue
import os
import sys
from threading import Timer
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, ShellBot, Speaker, SpaceFactory

my_mouth = Queue()
my_bot = ShellBot(mouth=my_mouth)


class SpeakerTests(unittest.TestCase):

    def tearDown(self):
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        bot = my_bot
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

        bot = my_bot
        bot.space = SpaceFactory.get('local', bot=bot)
        bot.space.id = '123'

        items = ['hello', 'world']
        for item in items:
            bot.mouth.put(item)
        bot.mouth.put(Exception('EOQ'))

        speaker = Speaker(bot=bot)

        with mock.patch.object(bot.space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.work()
            mocked.assert_any_call('hello')
            mocked.assert_called_with('world')

            with self.assertRaises(Exception):
                mouth.get_nowait()

    def test_run(self):

        logging.info("*** run")

        bot = my_bot
        bot.space = SpaceFactory.get('local', bot=bot)
        bot.space.id = '123'
        bot.mouth.put('ping')

        def my_post(item):
            logging.info("- speaking")
            bot.context.set('speaker.last', item)

        bot.space.post_message = my_post
        bot.context.set('general.switch', 'on')
        bot.context.set('speaker.counter', 0) # do not wait for run()

        speaker = Speaker(bot=bot)
        speaker_process = speaker.run()
        while True:
            counter = bot.context.get('speaker.counter', 0)
            if counter > 0:
                logging.info("- speaker.counter > 0")
                break
        bot.context.set('general.switch', 'off')
        speaker_process.join()

        self.assertEqual(bot.context.get('speaker.counter'), 1)
        self.assertEqual(bot.context.get('speaker.last'), 'ping')

    def test_work(self):

        logging.info("*** work")

        bot = my_bot
        bot.space = SpaceFactory.get('local', bot=bot)

        bot.space.id = '123'

        bot.speaker.process = mock.Mock(side_effect=Exception('TEST'))
        bot.mouth.put(('dummy'))
        bot.mouth.put(Exception('EOQ'))
        bot.speaker.work()
        self.assertEqual(bot.context.get('speaker.counter'), 0)

        bot.speaker = Speaker(bot=bot)
        bot.speaker.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        bot.mouth.put(('dummy'))
        bot.speaker.work()
        self.assertEqual(bot.context.get('speaker.counter'), 0)

    def test_work_wait(self):

        logging.info("*** work/wait while empty and not ready")

        bot = my_bot
        bot.space = SpaceFactory.get('local', bot=bot)

        bot.speaker.NOT_READY_DELAY = 0.01
        bot.context.set('general.switch', 'on')
        speaker_process = Process(target=bot.speaker.work)
        speaker_process.daemon = True
        speaker_process.start()

        t = Timer(0.1, bot.mouth.put, ['ping'])
        t.start()

        def set_ready(space, *args, **kwargs):
            space.id = '123'

        t = Timer(0.15, set_ready, [bot.space])
        t.start()

        time.sleep(0.2)
        bot.context.set('general.switch', 'off')
        speaker_process.join()

    def test_process(self):

        logging.info('*** process ***')

        bot = ShellBot()
        speaker = Speaker(bot=bot)

        speaker.process('hello world')  # sent to stdout

        bot = my_bot
        bot.space = SpaceFactory.get('local', bot=bot)
        bot.space.id = '123'

        speaker = Speaker(bot=bot)

        with mock.patch.object(bot.space,
                               'post_message',
                               return_value=None) as mocked:

            speaker.process('hello world')
            mocked.assert_called_with('hello world')

            class WithContent(object):
                text = ''
                content = 'me **too**'
                file = None

            item = WithContent()
            speaker.process(item)
            mocked.assert_called_with('',
                                      content='me **too**',
                                      file=None)

            class WithFile(object):
                text = '*with*attachment'
                content = None
                file = 'http://a.server/with/file'

            item = WithFile()
            speaker.process(item)
            mocked.assert_called_with('*with*attachment',
                                      content=None,
                                      file='http://a.server/with/file')

            class WithAll(object):
                text = 'hello world'
                content = 'hello **world**'
                file = 'http://a.server/with/file'

            item = WithAll()
            speaker.process(item)
            mocked.assert_called_with('hello world',
                                      content='hello **world**',
                                      file='http://a.server/with/file')

            class WithAllAndInit(object):
                def __init__(self, text, content, file):
                    self.text = text
                    self.content = content
                    self.file = file

            item = WithAllAndInit(text = 'hello world',
                                  content = 'hello **world**',
                                  file = 'http://a.server/with/file')
            speaker.process(item)
            mocked.assert_called_with('hello world',
                                      content='hello **world**',
                                      file='http://a.server/with/file')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
