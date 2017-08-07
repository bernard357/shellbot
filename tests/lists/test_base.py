#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
from multiprocessing import Manager, Process
import os
import random
import sys
import time

from shellbot import Context
from shellbot.lists import List


class ListTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()

    def tearDown(self):
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('***** init')

        list = List()
        self.assertEqual(list.context, None)

        list = List(context=self.context)
        self.assertEqual(list.context, self.context)

    def test_on_init(self):

        logging.info('***** on_init')

        list = List(items=['a', 'b', 'c'])
        self.assertEqual(list.items, ['a', 'b', 'c'])

    def test_iter(self):

        logging.info('***** __iter__')

        my_items = List(items=['a', 'b', 'c'])
        for (index, item) in enumerate(my_items):
            assert item == ['a', 'b', 'c'][index]


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
