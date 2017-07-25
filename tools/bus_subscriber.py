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

# you can run multiple instances of this program and see message replication
# done by ZeroMQ

bus = Bus(context=Context())
bus.check()

subscriber = bus.subscribe(['topic_A', 'topic_B'])

logging.info("Waiting for messages (non-blocking mode)")
while True:
    time.sleep(0.01)
    message = subscriber.get()
    if message:
        logging.info("- receiving: {}".format(message))
        if isinstance(message, dict):
            logging.info("- visible keys: {}".format(message.keys()))
        if str(message) == 'quit':
            logging.info("- stopping subscriber")
            break

logging.info("Waiting for messages (blocking mode)")
while True:
    message = subscriber.get(block=True)
    logging.info("- receiving: {}".format(message))
    if isinstance(message, dict):
        logging.info("- visible keys: {}".format(message.keys()))
    if str(message) == 'quit':
        logging.info("- stopping subscriber")
        break
