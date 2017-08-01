#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
from multiprocessing import Process
import sys
import time

from shellbot import Context
from shellbot.spaces import SpaceFactory


class SpaceFactoryTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()

    def tearDown(self):
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_build_space(self):

        logging.info("***** build generic space from settings")

        self.context.apply(settings={  # from settings to member attributes
            'space': {
                'title': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        space = SpaceFactory.build(context=self.context)
        self.assertEqual(self.context.get('space.title'), 'My preferred channel')
        self.assertEqual(space.configured_title(), 'My preferred channel')

    def test_build_local(self):

        logging.info("***** build local space from settings")

        self.context.apply(settings={  # from settings to member attributes
            'space': {
                'title': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'input': ['help', 'version'],
            }
        })

        space = SpaceFactory.build(context=self.context)
        self.assertEqual(self.context.get('space.title'), 'My preferred channel')
        self.assertEqual(space.configured_title(), 'My preferred channel')

    def test_build_spark(self):

        logging.info("***** build Cisco Spark space from settings")

        self.context.apply(settings={  # from settings to member attributes
            'spark': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODVGlZWU1NmYtyY',
            }
        })

        space = SpaceFactory.build(context=self.context)
        self.assertEqual(space.get('token'), 'hkNWEtMJNkODVGlZWU1NmYtyY')
        self.assertEqual(self.context.get('spark.room'), 'My preferred channel')
        self.assertEqual(space.configured_title(), 'My preferred channel')

    def test_sense_space(self):

        logging.info("***** sense generic space")

        self.context.apply(settings={  # sense='space'
            'space': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            }
        })

        self.assertEqual(SpaceFactory.sense(self.context), 'space')

    def test_sense_local(self):

        logging.info("***** sense local space")

        self.context.apply(settings={  # sense='local'
            'space': {
                'title': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'input': ['help', 'version'],
            }
        })

        self.assertEqual(SpaceFactory.sense(self.context), 'space')

    def test_sense_spark(self):

        logging.info("***** sense Cisco Spark space")

        self.context.apply(settings={  # sense='spark'
            'spark': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            }
        })

        self.assertEqual(SpaceFactory.sense(self.context), 'spark')

    def test_sense_alphabetical(self):

        logging.info("***** sense first space in alphabetical order")

        self.context.apply(settings={  # 'space' is coming before 'spark'
            'spark': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            },

            'space': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            },
        })

        self.assertEqual(SpaceFactory.sense(self.context), 'space')

        self.context.apply(settings={  # 'space' is coming before 'spark'
            'space': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            },

            'spark': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            },
        })

        self.assertEqual(SpaceFactory.sense(self.context), 'space')

    def test_sense_void(self):

        logging.info("***** sense nothing on bad configuration")

        self.context.apply(settings={  # no recognizable space type
            'not_a_space_type': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            },

            'neither_me': {
                'room': 'My preferred channel',
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
            },
        })

        with self.assertRaises(ValueError):
            SpaceFactory.sense(self.context)

    def test_get_space(self):

        logging.info("***** get generic space")

        space = SpaceFactory.get(type='space')
        self.assertEqual(space.prefix, 'space')

        space = SpaceFactory.get(type='space', context='c', weird='w')
        self.assertEqual(space.context, 'c')
        with self.assertRaises(AttributeError):
            self.assertEqual(space.weird, 'w')
        self.assertEqual(space.prefix, 'space')

    def test_get_local(self):

        logging.info("***** get local space")

        space = SpaceFactory.get(type='local', input=['hello', 'world'])
        self.assertEqual(space.prefix, 'space')
        self.assertEqual(space.participants, [])

    def test_get_spark(self):

        logging.info("***** get Cisco Spark space")

        space = SpaceFactory.get(type='spark', context=self.context, token='b')
        self.assertEqual(space.get('token'), 'b')

    def test_get_unknown(self):

        logging.info("***** get invalid space")

        with self.assertRaises(ValueError):
            space = SpaceFactory.get(type='*unknown', ex_token='b', ex_ears='c')


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
