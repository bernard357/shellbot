#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import sys
import time

from shellbot import Context
from shellbot.bus import Bus, Subscriber, Publisher

Context.set_logger()

# this should be ran manually for test purpose

bus = Bus(context=Context())

items = [
    ('topic_A', 'hello'),
    ('topic_B', 'world'),
    ('topic_C', 'should not be received'),
    ('topic_B', 'life'),
    ('topic_A', 'is good'),
    ('topic_D', 'should not pop up either'),
    (['topic_A', 'topic_B'], 'should be received twice'),
    (['topic_X', 'topic_B', 'topic_Y'], 'should be received once'),
    ('topic_E', 'filtered, again'),
    ('topic_A', {'hello': 'world'}),
    ('topic_B', {'greetings': ['hello', 'bonjour', 'salute'], 'thanks': ['thanks', 'merci']}),
    ('topic_Z', {'hidden': 'data'}),
    ('topic_A', 'quit'),
]

publisher = bus.publish()

logging.info("Please run bus_subscriber one or more times")
time.sleep(3.0)

logging.info("Sending messages")

for index in range(2):
    for topic, message in items:
        logging.info("- sending: {} {}".format(topic, message))
        publisher.put(topic, message)
        time.sleep(0.3)

logging.info("All messages have been sent")
