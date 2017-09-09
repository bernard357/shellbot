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

    - name: SupportTeam
      as_command: true
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


class ListFactoryTests(unittest.TestCase):

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
        self.assertEqual(sorted(factory.lists.keys()), ['supportteam', 'the famous four'])

        settings = yaml.load(dict_instead_of_list_yaml )
        self.context.clear()
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(len(factory.lists.keys()), 0)

        settings = yaml.load(list_instead_of_dict_yaml )
        self.context.clear()
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(len(factory.lists.keys()), 0)

        settings = yaml.load(missing_names_yaml )
        self.context.clear()
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()
        self.assertEqual(len(factory.lists.keys()), 0)

    def test_build_list(self):

        logging.info("***** build_list")

        factory = ListFactory(self.context)

        with self.assertRaises(AssertionError):
            list = factory.build_list(None)
        with self.assertRaises(AssertionError):
            list = factory.build_list('*weird')

        list = factory.build_list({})
        self.assertEqual(list.items, [])
        self.assertEqual(list.as_command, False)

        list = factory.build_list(
            {'items': ['service.desk@acme.com', 'supervisor@brother.mil'],
             'as_command': True})
        self.assertEqual(list.items,
                         ['service.desk@acme.com', 'supervisor@brother.mil'])
        self.assertEqual(list.as_command, True)

    def test_get_list(self):

        logging.info("***** get_list")

        factory = ListFactory(self.context)

        settings = yaml.load(my_yaml)
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()

        list = factory.get_list("*unknown")
        self.assertEqual(list, [])

        list = factory.get_list("The Famous Four")
        self.assertEqual(list.items, ['alice@acme.com', 'bob@project.org', 'celine@secret.mil', 'dude@bangkok.travel'])

        list = factory.get_list("the famous four")
        self.assertEqual(list.items, ['alice@acme.com', 'bob@project.org', 'celine@secret.mil', 'dude@bangkok.travel'])

        list = factory.get_list("SupportTeam")
        self.assertEqual(list.items, ['service.desk@acme.com', 'supervisor@brother.mil'])

        list = factory.get_list("supportteam")
        self.assertEqual(list.items, ['service.desk@acme.com', 'supervisor@brother.mil'])

    def test_list_commands(self):

        logging.info("***** list_commands")

        factory = ListFactory(self.context)

        settings = yaml.load(my_yaml)
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()

        names = [x for x in factory.list_commands()]
        self.assertEqual(sorted(names), ['SupportTeam'])

    def test_apply_to_list(self):

        logging.info("***** aply_to_list")

        factory = ListFactory(self.context)

        settings = yaml.load(my_yaml)
        self.context.apply(settings)
        factory = ListFactory(context=self.context)
        factory.configure()

        class Counter(object):
            value = 0

            def consume(self, item):
                logging.debug(u"- {}".format(item))
                self.value += 1

        my_counter = Counter()

        factory.apply_to_list(name='SupportTeam',
                              apply=lambda x: my_counter.consume(x))
        self.assertEqual(my_counter.value, 2)

        factory.apply_to_list(name='supportteam',
                              apply=lambda x: my_counter.consume(x))
        self.assertEqual(my_counter.value, 4)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
