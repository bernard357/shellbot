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


class ExampleTests(unittest.TestCase):

    def test_linear_state_initial(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'initial.state': 'T100'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from examples.linear.state import State

        c = State(shell)

        self.assertEqual(c.keyword, 'state')
        self.assertEqual(c.information_message, 'Display process current state.')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'Current state: T100')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_linear_state_current(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'current.state': 'T200'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from examples.linear.state import State

        c = State(shell)

        self.assertEqual(c.keyword, 'state')
        self.assertEqual(c.information_message, 'Display process current state.')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'Current state: T200')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_linear_next_current(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'current.state': 'T200'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from examples.linear.next import Next

        c = Next(shell)

        self.assertEqual(c.keyword, 'next')
        self.assertEqual(c.information_message, 'Move process to next state.')
        self.assertTrue(c.is_interactive)
        self.assertFalse(c.is_hidden)

        c.execute()
        self.assertEqual(mouth.get(), 'New state: T300')
        with self.assertRaises(Exception):
            mouth.get_nowait()

    def test_linear_lifecycle(self):

        settings = {
            'process': {
                'states': ['T100', 'T200', 'T300'],
                'current.state': 'T100'
            }
        }

        context = Context(settings)
        mouth = Queue()
        shell = Shell(context, mouth)

        from examples.linear.state import State
        from examples.linear.next import Next

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

    Context.set_logger()
    sys.exit(unittest.main())
