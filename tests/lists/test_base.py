#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
from multiprocessing import Manager, Process
import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath('..'))

from shellbot import Context
from shellbot.lists import List


my_context = Context()


class ListTests(unittest.TestCase):

    def test_init(self):

        logging.info('***** init')

        list = List()
        self.assertEqual(list.context, None)

        list = List(context=my_context)
        self.assertEqual(list.context, my_context)

    def test_on_init(self):

        logging.info('***** on_init')

        list = List(items=['a', 'b', 'c'])
        self.assertEqual(list.items, ['a', 'b', 'c'])

    def test_iter(self):

        logging.info('***** __iter__')

        list = List(items=['a', 'b', 'c'])
        index = 0
        for item in list:
            assert item == ['a', 'b', 'c'][index]
            index += 1


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
