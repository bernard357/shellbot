#!/usr/bin/env python

import colorlog
import logging
import os
import sys
import time
from bottle import route, run, request, abort

sys.path.insert(0, os.path.abspath('..'))

from shellbot.bot import ShellBot
from shellbot.context import Context
from shellbot.commands.base import Command

handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(
    "%(asctime)-2s %(log_color)s%(message)s",
    datefmt='%H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)
handler.setFormatter(formatter)

logging.getLogger('').handlers = []
logging.getLogger('').addHandler(handler)

logging.getLogger('').setLevel(level=logging.DEBUG)


class Batman(Command):
    keyword = 'whoareyou'
    information_message = "I'm Batman!"


class Batcave(Command):
    keyword = 'cave'
    information_message = "The Batcave is silent..."

    def execute(self, arguments=None):
        if arguments:
            self.shell.say("The Batcave echoes, '{0}'".format(arguments))
        else:
            self.shell.say(self.information_message)


class Batsignal(Command):
    keyword = 'signal'
    information_message = "NANA NANA NANA NANA"
    information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

    def execute(self, arguments=None):
        self.shell.say(self.information_message,
                       file=self.information_file)


class Batsuicide(Command):
    keyword = 'suicide'
    information_message = "Going back to Hell"

    def execute(self, arguments=None):
        self.shell.say(self.information_message)
        self.context.set('general.signal', 'suicide')


bot = ShellBot()
bot.shell.load_commands([Batman(), Batcave(), Batsignal(), Batsuicide()])

settings = {

    'bot': {
        'on_start': 'You can now chat with Batman',
        'on_stop': 'Batman is now quitting the room, bye',
    },

    'spark': {
        'room': 'Chat with Batman',
        'moderators': 'bernard.paques@dimensiondata.com',
#        'webhook': 'http://518c74cc.ngrok.io',
    },

}

bot.configure_from_dict(settings)

bot.space.connect()
bot.space.dispose(bot.context.get('spark.room'))

bot.start()

while True:

    time.sleep(1)
    signal = bot.context.get('general.signal')
    if signal is not None:
        bot.stop()
        time.sleep(5)
        bot.space.dispose(bot.context.get('spark.room'))
        break



