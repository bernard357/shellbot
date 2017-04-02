#!/usr/bin/env python

import unittest
import logging
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.shell import Shell


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
        self.assertEqual(c.usage_message, 'state')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        self.assertTrue(c.execute(''))
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
        self.assertEqual(c.usage_message, 'state')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        self.assertTrue(c.execute(''))
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
        self.assertEqual(c.usage_message, 'next')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        self.assertTrue(c.execute(''))
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

        self.assertTrue(s.execute(''))
        self.assertEqual(mouth.get(), 'Current state: T100')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(n.execute(''))
        self.assertEqual(mouth.get(), 'New state: T200')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(s.execute(''))
        self.assertEqual(mouth.get(), 'Current state: T200')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(n.execute(''))
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(s.execute(''))
        self.assertEqual(mouth.get(), 'Current state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(n.execute(''))
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(s.execute(''))
        self.assertEqual(mouth.get(), 'Current state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

        self.assertTrue(n.execute(''))
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
