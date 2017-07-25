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
bus.check()

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

logging.info("Sending messages")

for index in range(2):
    for topic, message in items:
        logging.info("- sending: {} {}".format(topic, message))
        publisher.put(topic, message)

logging.info("All messages have been sent")

publisher.fan.put(None)

logging.info("Assume you run bus_spy in a separate procees to see the outcome")
time.sleep(1.0)

publisher.start()
publisher.join()

bus.context.set('general.switch', 'off')
time.sleep(0.5)
