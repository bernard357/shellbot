#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from multiprocessing import Process, Queue
import time

from shellbot import ShellBot, Context, Server, Notify, Wrap
Context.set_logger()

# load configuration
settings = {
    'bot': {
        'on_start': u'Support digital au processus de dérogation',
        'on_stop':  u'Fermeture du procesus, merci et aurevoir',
    },
    'spark': {
        'room': '[' + os.environ["POD_NAME"] + '] Derogation',
        'moderators': os.environ["CHAT_ROOM_MODERATORS"],
    },
    'server': {
        'url':     os.environ["SERVER_URL"],
        'trigger': os.environ["SERVER_TRIGGER"],
        'hook':    os.environ["SERVER_HOOK"],
        'binding': os.environ["SERVER_HOST"],
        'port':    os.environ["SERVER_PORT"],
    },
    'process.steps': [
        {
            'label': u'Niveau 1',
            'message': u'Collecte des informations essentielles',
            'content': u'\n---\nL\'espace d\'échange a été initialisé.\n'
                + u'\n'
                + u'Rappel: \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' help** pour avoir la liste des commandes disponibles \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' step** pour passer à l\'étape suivante \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' input** pour connaitre les informations collectées \n',
            'participants': os.environ["E2E"],
        },
        {
            'label': u'Niveau 2',
            'message': u'Choix de l\'action à réaliser',
            'content': u'\n---\nMerci de choisir une des non-conformités en indiquant sa référence \n'
                + u'\n'
                + u'Rappel: \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' help** pour avoir la liste des commandes disponibles \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' step** pour passer à l\'étape suivante \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' input** pour connaitre les informations collectées \n'
                + u'* Utiliser le menu de Spark pour: Ajouter un partitcipant, Passer un appel de groupe, Lister les fichiers... \n',
        },
        {
            'label': u'Niveau 3',
            'message': u'Statut et archivage',
            'content': u'\n---\nMerci de choisir un statut du dossier afin d\'archiver cet espace: \n'
                + u'\n'
                + u'Rappel: \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' help** pour avoir la liste des commandes disponibles \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' step** pour passer à l\'étape suivante \n'
                + u'* Utiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' input** pour connaitre les informations collectées \n',
        },
        {
            'label': u'Terminé!',
            'message': u'Fermeture de cet espace',
            'content': u'\n---\nUtiliser la commande **@' + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u' close** pour fermer **définitivement** cet espace',
        },
    ],
}
context = Context(settings)
context.check('server.trigger', os.environ["SERVER_TRIGGER"])
context.check('server.hook', os.environ["SERVER_HOOK"])

# create a bot and load commands
bot = ShellBot(context=context, configure=True)
bot.load_command('shellbot.commands.close') # allow space deletion from chat

# audit all interactions in a separate file
from shellbot.commands import Audit
audit = Audit(bot=bot)
bot.load_command(audit)  # manage auditing

from shellbot.updaters import FileUpdater
audit.arm(updater=FileUpdater(path=(os.environ["SERVER_LOG"])))

# ask information from end user
bot.load_command('shellbot.commands.input') # reflect information gathered
bot.load_command('shellbot.commands.update')
from shellbot.machines import Input, Sequence
from shellbot.machines import Menu, Sequence

## Sequence of the Step 1 (collecte)
AM = Input(bot=bot,
                question = u'/!\ Merci de fournir le numéro **AM** \n',
                mask="AM9999999",
                on_retry = u"Le numero AM doit commencer par AM et doit comporter 7 chiffres.",
                on_answer = u"Le numéro AM a été enregistré: {}",
                on_cancel = u"Le numéro AM est obligatoire",
                tip=15,
                timeout=0,
                key='AM')

localisation = Input(bot=bot,
                question=u"/!\ Merci de fournir la localisation (programme tronçon MSN)",
                mask="AA A99 MSN9999999",
                on_retry=u"La localisation doit comporter une des références suivantes: \n"
                       + u"* programme: XW, SA, LR, MA, LA \n"
                       + u"* tronçon: T11, T12, B11/12, B13/14 \n"
                       + u"* MSN: MSN1234567 \n",
                on_answer=u"La localisation a été enregistrée: {}",
                on_cancel=u"La localisation est obligatoire",
                tip=15,
                timeout=0,
                key='localisation')

conformite = Menu(bot=bot,
                question=u"/!\ Merci de choisir une des non-conformités ci-dessous grace à sa référence: \n",
                options=[ u"AAAAA", u"BBBBB", u"CCCCC" ],
                on_retry=u"Le chiffre entré doit correspondre à une des non-conformités listés précédemment.",
                on_answer=u"La non-conformité a été enregistrée: {}",
                on_cancel=u"La non-conformité est obligatoire",
                tip=15,
                timeout=0,
                key='conformite')

localisation_avion = Input(bot=bot,
                question=u"/!\ Merci de fournir la localisation avion \n"
                       + u"La localisation avion est un text libre et n'est pas obligatoire",
                on_retry=u"La localisation avion doit correspondre à une référence de cadre/lisse.",
                on_answer=u"Ok, localisation avion enregistrée: {}.\n\nPensez à passer à la prochaine étape: @" + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u" step",
                on_cancel=u"La localisation avion est manquante mais n'est pas obligatoire.\n\nPensez à passer à la prochaine étape: @" + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u" step",
                tip=15,
                timeout=40,
                key='localisation_avion')

## Sequence of the Step 2 (action) 
photo = Input(bot=bot,
                question=u"/!\ Merci de prendre une photo de la pièce défectueuse et d'y ajouter une description \n",
                on_retry=u"Utilisez l\'icone + pour prendre une photo.",
                on_answer=u"La photo a été enregistrée: {}",
                on_cancel=u"La photo est manquante mais n'est pas obligatoire",
                tip=15,
                timeout=40,
                key='photo')

Txxx = Menu(bot=bot,
                question=u"/!\ Merci de fournir la prochaine étape à l'aide de sa référence",
                options=[ u"T200", u"T300", u"T400"],
                on_retry=u"Le chiffre entré doit correspondre à une des références Txxx listés précédemment.",
                on_answer=u"L'étape a été enregistrée mais le service n'est pas encore opérationnel: {}.\n\nPensez à passer à la prochaine étape: @" + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u" step",
                on_cancel=u"L'étape est manquante mais n'est pas obligatoire. \n\Passer à la prochaine étape: @" + str(os.environ["CISCO_SPARK_BOT_NAME"]) + u" step",
                tip=15,
                timeout=40,
                key='Txxx')

## Sequence of the Step 3 (status & archiving)
status = Input(bot=bot,
                question=u"/!\ Merci de fournir l'état du dossier pour son archivage: \n"
                       + u"1. Ok \n"
                       + u"2. Rejeté \n"
                       + u"3. Annulé \n"
                       + u"Text libre \n",
                mask="A",
                on_retry=u"Le chiffre entré doit correspondre à un des status listés précédemment.",
                on_answer=u"Le statut a été enregistré: {}.\n\nProcessus complété.",
                on_cancel=u"Le statut est manquant et est une information obligatoire",
                tip=15,
                timeout=0,
                key='status')

# implement the Step process
bot.load_command('shellbot.commands.step') # progress to next step of process
steps = bot.get('process.steps', [])
steps[0]['machine'] = Sequence(machines=[AM, localisation, conformite, localisation_avion])
steps[1]['machine'] = Sequence(machines=[photo, Txxx])
steps[2]['machine'] = Sequence(machines=[status])

from shellbot.machines import Steps
bot.machine = Steps(bot=bot, steps=steps)

# a queue of events between the web server and the bot
queue = Queue()

# create a web server to receive triggers and updates
server = Server(context=context, check=True)
server.add_route(Notify(queue=queue, route=context.get('server.trigger')))
server.add_route(Wrap(callable=bot.get_hook(), route=context.get('server.hook')))

# delay the creation of a room until we receive some trigger
class Trigger(object):

    EMPTY_DELAY = 0.005   # time to wait if queue is empty

    def __init__(self, bot, queue):
        self.bot = bot
        self.queue = queue if queue else Queue()

    def work(self):

        logging.info(u"Waiting for trigger")

        try:
            self.bot.context.set('trigger.counter', 0)
            while self.bot.context.get('general.switch', 'on') == 'on':

                if self.queue.empty():
                    time.sleep(self.EMPTY_DELAY)
                    continue

                try:
                    item = self.queue.get(True, self.EMPTY_DELAY)
                    if isinstance(item, Exception):
                        break

                    self.process(item)

                except Exception as feedback:
                    logging.exception(feedback)

        except KeyboardInterrupt:
            pass

    def process(self, item):

        counter = self.bot.context.increment('trigger.counter')
        logging.info(u'Trigger {} {}'.format(item, counter))

        if counter == 1:
            self.bot.bond()
            self.bot.space.on_run()
            self.bot.hook()

            time.sleep(2)
            self.bot.machine.reset()
            self.bot.machine.start()

    def on_dispose(self):
        logging.debug(u"- stopping the machine")
        self.bot.machine.stop()
        logging.debug(u"- resetting the counter of button pushes")
        self.bot.set('trigger.counter', 0)

trigger = Trigger(bot, queue)

bot.register('dispose', trigger)

#
# launch multiple processes to do the job
#

bot.start()

p = Process(target=trigger.work)
#p.daemon = True
p.start()

server.run()
