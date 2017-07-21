#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
from multiprocessing import Process, Queue
import sys

from shellbot import Context, Engine, ShellBot, SpaceFactory
from examples.planets import Rocket


class MyRocket(Rocket):

    def process(self, item):
        self.bot.engine.set('processed', item)


class RocketTests(unittest.TestCase):

    def setUp(self):
        self.engine = Engine(mouth=Queue())
        self.bot = ShellBot(engine=self.engine, channel_id='*id')
        self.rocket = MyRocket(bot=self.bot)

    def tearDown(self):
        del self.rocket
        del self.bot
        del self.engine
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        rocket_process = self.rocket.start()

        rocket_process.join(0.01)
        if rocket_process.is_alive():
            logging.info('Stopping rocket')
            self.engine.set('general.switch', 'off')
            rocket_process.join()

        self.assertFalse(rocket_process.is_alive())

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        self.rocket.inbox.put(('explore', 'Moon'))
        self.rocket.inbox.put(None)
        self.rocket.run()

        self.assertEqual(self.engine.get('processed'), ('explore', 'Moon'))

        with self.assertRaises(Exception):
            print(self.engine.mouth.get_nowait())

    def test_run(self):

        logging.info("*** run")

        rocket = Rocket(bot=self.bot)
        rocket.process = mock.Mock(side_effect=Exception('TEST'))
        rocket.inbox.put(('explore', 'Moon'))
        rocket.inbox.put(None)
        rocket.run()

        self.engine.context.clear()
        rocket = Rocket(bot=self.bot)
        rocket.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        rocket.inbox.put(('explore', 'Moon'))
        rocket.run()

    def test_process(self):

        logging.info("*** process")

        rocket = Rocket(bot=self.bot)

        with self.assertRaises(AssertionError):
            rocket.process(('*unknwon_verb', 'Moon'))

        rocket.process(('explore', '*alien_planet'))
        self.assertEqual(self.engine.mouth.get().text,
                         "Planet '*alien_planet' is unknown")



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
