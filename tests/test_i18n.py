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
from shellbot.i18n import Localization, localization as l10n, _

class LocalizationTests(unittest.TestCase):

    def test_default(self):

        logging.info('*** default ***')

        localization = Localization()
        text = 'hello world'
        self.assertEqual(localization._(text), text)

    def test_init(self):

        logging.info('*** init ***')

        settings = {

            'localized': {
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

        my_localization = Localization(context)
        self.assertEqual(my_localization.context, context)

        self.assertEqual(my_localization._('hello world'), "What'up, Doc?")
        self.assertEqual(my_localization._('not localized'), 'not localized')
        self.assertEqual(my_localization.actual_strings,
                         {'hello world': "What'up, Doc?",
                          'not localized': 'not localized'})

    def test_global(self):

        logging.info('*** global ***')

        settings = {

            'localized': {
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

        l10n.set_context(context)
        self.assertEqual(l10n.actual_strings, {})

        self.assertEqual(_('hello world'), "What'up, Doc?")
        self.assertEqual(l10n.actual_strings,
                         {'hello world': "What'up, Doc?"})

        self.assertEqual(_('not localized'), 'not localized')
        self.assertEqual(l10n.actual_strings,
                         {'hello world': "What'up, Doc?",
                          'not localized': 'not localized'})

        self.assertEqual(_('another string'), 'Bye!')
        self.assertEqual(l10n.actual_strings,
                         {'hello world': "What'up, Doc?",
                          'another string': 'Bye!',
                          'not localized': 'not localized'})


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
