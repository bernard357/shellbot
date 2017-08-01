#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import mock
import os
import sys
import time
import yaml

from shellbot import Context
from shellbot.lists import ListFactory


my_yaml = """

lists:

    - name: The Famous Four
      items:
        - alice@acme.com
        - bob@project.org
        - celine@secret.mil
        - dude@bangkok.travel

    - name: Support Team
      items:
        - service.desk@acme.com
        - supervisor@brother.mil

"""

dict_instead_of_list_yaml = """

lists:

    "The Famous Four":
      items:
        - alice@acme.com
        - bob@project.org
        - celine@secret.mil
        - dude@bangkok.travel

    "Support Team":
      items:
        - service.desk@acme.com
        - supervisor@brother.mil

"""

list_instead_of_dict_yaml = """

lists:

    - - name: The Famous Four
      - items:
          - alice@acme.com
          - bob@project.org
          - celine@secret.mil
          - dude@bangkok.travel

    - - name: Support Team
      - items:
          - service.desk@acme.com
          - supervisor@brother.mil

"""

missing_names_yaml = """

lists:

    - items:
        - alice@acme.com
        - bob@project.org
        - celine@secret.mil
        - dude@bangkok.travel

    - items:
        - service.desk@acme.com
        - supervisor@brother.mil

"""


class StoreFactoryTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()

    def tearDown(self):
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info("***** init")

        factory = ListFactory(context='a')
        self.assertEqual(factory.context, 'a')
        self.assertEqual(factory.lists, {})

        factory = ListFactory(context=self.context)
        self.assertEqual(factory.context, self.context)
        self.assertEqual(factory.lists, {})

    def test_configure(self):

        logging.info("***** configure")

        settings = yaml.load(my_yaml)
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(factory.lists.keys(), ['Support Team', 'The Famous Four'])

        settings = yaml.load(dict_instead_of_list_yaml )
        self.context.clear()
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(factory.lists.keys(), [])

        settings = yaml.load(list_instead_of_dict_yaml )
        self.context.clear()
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(factory.lists.keys(), [])

        settings = yaml.load(missing_names_yaml )
        self.context.clear()
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(factory.lists.keys(), [])

    def test_build_list(self):

        logging.info("***** build_list")

        factory = ListFactory(self.context)

        with self.assertRaises(AssertionError):
            list = factory.build_list(None)
        with self.assertRaises(AssertionError):
            list = factory.build_list('*weird')

        list = factory.build_list({})
        self.assertEqual(list.items, [])

        list = factory.build_list(
            {'items': ['service.desk@acme.com', 'supervisor@brother.mil']})
        self.assertEqual(list.items, ['service.desk@acme.com', 'supervisor@brother.mil'])

    def test_get_list(self):

        logging.info("***** get_list")

        factory = ListFactory(self.context)

        settings = yaml.load(my_yaml)
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()

        list =  factory.get_list("*unknown")
        self.assertEqual(list, [])

        list =  factory.get_list("The Famous Four")
        self.assertEqual(list.items, ['alice@acme.com', 'bob@project.org', 'celine@secret.mil', 'dude@bangkok.travel'])

        list =  factory.get_list("Support Team")
        self.assertEqual(list.items, ['service.desk@acme.com', 'supervisor@brother.mil'])


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
