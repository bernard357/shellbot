#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context, Engine, ShellBot, SpaceFactory
from examples.planets import Rocket

my_engine = Engine(mouth=Queue(),
                   space=SpaceFactory.get('local'))
my_bot = ShellBot(engine=my_engine)


class MyRocket(Rocket):

    def process(self, item):
        self.bot.engine.set('processed', item)


my_rocket = MyRocket(bot=my_bot)


class RocketTests(unittest.TestCase):

    def tearDown(self):
        my_engine.context.clear()
        collected = gc.collect()
        logging.info("Garbage collector: collected %d objects." % (collected))

    def test_static(self):

        logging.info('*** Static test ***')

        rocket_process = my_rocket.start()

        rocket_process.join(0.01)
        if rocket_process.is_alive():
            logging.info('Stopping rocket')
            my_engine.set('general.switch', 'off')
            rocket_process.join()

        self.assertFalse(rocket_process.is_alive())

    def test_dynamic(self):

        logging.info('*** Dynamic test ***')

        my_rocket.inbox.put(('explore', 'Moon'))
        my_rocket.inbox.put(None)
        my_rocket.run()

        self.assertEqual(my_engine.get('processed'), ('explore', 'Moon'))

        with self.assertRaises(Exception):
            print(my_engine.mouth.get_nowait())

    def test_run(self):

        logging.info("*** run")

        rocket = Rocket(bot=my_bot)
        rocket.process = mock.Mock(side_effect=Exception('TEST'))
        rocket.inbox.put(('explore', 'Moon'))
        rocket.inbox.put(None)
        rocket.run()

        my_engine.context.clear()
        rocket = Rocket(bot=my_bot)
        rocket.process = mock.Mock(side_effect=KeyboardInterrupt('ctl-C'))
        rocket.inbox.put(('explore', 'Moon'))
        rocket.run()

    def test_process(self):

        logging.info("*** process")

        rocket = Rocket(bot=my_bot)

        with self.assertRaises(AssertionError):
            rocket.process(('*unknwon_verb', 'Moon'))

        rocket.process(('explore', '*alien_planet'))
        self.assertEqual(my_engine.mouth.get().text,
                         "Planet '*alien_planet' is unknown")



if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
