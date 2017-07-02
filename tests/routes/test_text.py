#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
from multiprocessing import Queue
import sys

sys.path.insert(0, os.path.abspath('../..'))

from shellbot import Context
from shellbot.routes.text import Text


class TextTests(unittest.TestCase):

    def test_text(self):

        r = Text(Context())
        self.assertEqual(r.route, '/')
        self.assertEqual(r.page, None)
        self.assertEqual(r.get(), 'OK')

        r = Text(Context(), route='/hello', page='Hello world')
        self.assertEqual(r.route, '/hello')
        self.assertEqual(r.page, 'Hello world')
        self.assertEqual(r.get(), 'Hello world')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
