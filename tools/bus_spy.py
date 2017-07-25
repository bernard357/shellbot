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

subscriber = bus.subscribe('')

logging.info("Waiting for messages, press Ctl-C to stop the program")
try:
    while True:
        message = subscriber.get(block=True)
        logging.info("- receiving: {}".format(message))
except KeyboardInterrupt:
    pass
