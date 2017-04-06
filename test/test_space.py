#!/usr/bin/env python

import unittest
import logging
import os
from multiprocessing import Process, Queue
import sys

sys.path.insert(0, os.path.abspath('..'))

from shellbot.context import Context
from shellbot.space import SparkSpace


class SpaceTests(unittest.TestCase):

    def test_init(self):

        space = SparkSpace(context='a', bearer='b', ears='c')
        self.assertEqual(space.context, 'a')
        self.assertEqual(space.bearer, 'b')
        self.assertEqual(space.ears, 'c')
        self.assertEqual(space.room_id, None)

        with self.assertRaises(Exception):
            space.dispose('*unknown*space*')

if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.exit(unittest.main())
