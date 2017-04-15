#!/usr/bin/env python
# -*- coding: utf-8 -*-

import colorlog
import unittest
import logging
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context, Shell


class CustomTests(unittest.TestCase):

    def test_exception_status_initial(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'initial': 'T100'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from custom.exception.state import State

        c = State(shell)

        self.assertEqual(c.keyword, 'state')
        self.assertEqual(c.information_message, 'Displays process current state.')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'Current state: T100')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_exception_status_current(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'current': 'T200'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from custom.exception.state import State

        c = State(shell)

        self.assertEqual(c.keyword, 'state')
        self.assertEqual(c.information_message, 'Displays process current state.')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'Current state: T200')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_exception_next_current(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'current': 'T200'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from custom.exception.next import Next

        c = Next(shell)

        self.assertEqual(c.keyword, 'next')
        self.assertEqual(c.information_message, 'Moves process to next state.')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_exception_sequence(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'current': 'T100'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from custom.exception.state import State
        from custom.exception.next import Next

        s = State(shell)
        n = Next(shell)

        s.execute()
        self.assertEqual(mouth.get(), 'Current state: T100')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        n.execute()
        self.assertEqual(mouth.get(), 'New state: T200')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        s.execute()
        self.assertEqual(mouth.get(), 'Current state: T200')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        n.execute()
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        s.execute()
        self.assertEqual(mouth.get(), 'Current state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        n.execute()
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        s.execute()
        self.assertEqual(mouth.get(), 'Current state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        n.execute()
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

if __name__ == '__main__':

    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(asctime)-2s %(log_color)s%(message)s",
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)

    logging.getLogger('').handlers = []
    logging.getLogger('').addHandler(handler)

    logging.getLogger('').setLevel(level=logging.DEBUG)

    sys.exit(unittest.main())
