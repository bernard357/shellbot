#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
import sys
import time

from shellbot import Context, Engine
from shellbot.i18n import Customization, _

class CustomizationTests(unittest.TestCase):

    def test_default(self):

        logging.info('*** default ***')

        customization = Customization()
        text = 'hello world'
        self.assertEqual(customization._(text), text)

    def test_init(self):

        logging.info('*** init ***')

        settings = {

            'customized': {
                'hello world': "What'up, Doc?",
                'another string': 'Bye!',
            },

            'space': {
                'title': 'space name',
                'participants': ['joe.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.no.where',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }
        context=Context(settings)

        customization = Customization(context)
        self.assertEqual(customization.context, context)

        self.assertEqual(customization._('hello world'), "What'up, Doc?")
        self.assertEqual(customization._('not customized'), 'not customized')
        self.assertEqual(customization.actual_strings,
                         {'hello world': "What'up, Doc?",
                          'not customized': 'not customized'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
