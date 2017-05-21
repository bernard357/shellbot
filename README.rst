========
Shellbot
========

.. image:: https://readthedocs.org/projects/shellbot-for-cisco-spark/badge/?version=latest
   :target: http://shellbot-for-cisco-spark.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/pypi/v/shellbot.svg
   :target: https://pypi.python.org/pypi/shellbot

.. image:: https://img.shields.io/travis/bernard357/shellbot.svg
   :target: https://travis-ci.org/bernard357/shellbot

.. image:: https://img.shields.io/badge/coverage-93%25-green.svg
   :target: https://img.shields.io/badge/coverage-93%25-green.svg

.. image:: https://img.shields.io/pypi/pyversions/shellbot.svg?maxAge=2592000
   :target: https://www.python.org/

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: http://www.apache.org/licenses/LICENSE-2.0


Fast, simple and lightweight micro bot-framework for Python.

Features
--------
* Comprehensive set of examples is included
* Create powerful state machines for mastering bot-human interactions
* Create the exact set of shell commands needed for your application
* Either respond interactively, or pipeline long-lasting commands
* Audit dynamically chat interactions
* Native support of Cisco Spark
* Local disconnected mode of operation for development and tests
* Bottle is included for easy interactions over the web
* Test coverage exceeds 90%
* Made for python 2.7 and for python 3.x
* Documentation: `Shellbot at ReadTheDocs`_
* Python package: `Shellbot at PyPi`_
* Source code: `Shellbot at GitHub`_
* Free software: `Apache License (2.0)`_

The Batman example
------------------

.. code-block:: python

    from shellbot import ShellBot, Context, Command

    # create a bot and load commands
    #

    class Batman(Command):
        keyword = 'whoareyou'
        information_message = u"I'm Batman!"

    class Batcave(Command):
        keyword = 'cave'
        information_message = u"The Batcave is silent..."

        def execute(self, arguments=None):
            if arguments:
                self.bot.say(u"The Batcave echoes, '{0}'".format(arguments))
            else:
                self.bot.say(self.information_message)

    class Batsignal(Command):
        keyword = 'signal'
        information_message = u"NANA NANA NANA NANA"
        information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

        def execute(self, arguments=None):
            self.bot.say(self.information_message,
                         file=self.information_file)

    class Batsuicide(Command):
        keyword = 'suicide'
        information_message = u"Go back to Hell"
        is_interactive = False

        def execute(self, arguments=None):
            time.sleep(3)
            self.bot.say(self.information_message)
            self.bot.stop()


    bot = ShellBot(commands=[Batman(), Batcave(), Batsignal(), Batsuicide()])

    # load configuration
    #
    os.environ['BOT_ON_START'] = 'You can now chat with Batman'
    os.environ['BOT_ON_STOP'] = 'Batman is now quitting the room, bye'
    os.environ['CHAT_ROOM_TITLE'] = 'Chat with Batman'
    bot.configure()

    # initialise a chat room
    #
    bot.bond(reset=True)

    # run the bot
    #
    bot.run()

    # delete the chat room when the bot is stopped
    #
    bot.dispose()


Quick installation
------------------

To install the shellbot package, type::

    $ pip install shellbot

Or, if you prefer to download the full project including examples and documentation,
and install it, do the following::

    $ git clone https://github.com/bernard357/shellbot.git
    $ cd shellbot
    $ pip install -e .

Credits
-------

* securitybot_ from the Dropbox team
* Bottle_
* ciscosparkapi_
* PyYAML_
* Cookiecutter_
* `cookiecutter-pypackage`_

.. _securitybot: https://github.com/dropbox/securitybot
.. _`Shellbot at ReadTheDocs`: http://shellbot-for-cisco-spark.readthedocs.io/en/latest/
.. _`Shellbot at PyPi`: https://pypi.python.org/pypi/shellbot
.. _`Shellbot at GitHub`: https://github.com/bernard357/shellbot
.. _`Apache License (2.0)`: http://www.apache.org/licenses/LICENSE-2.0
.. _`Bernard Paques`: https://github.com/bernard357
.. _`Anthony Shaw`: https://github.com/tonybaloney
.. _Bottle: https://pypi.python.org/pypi/bottle
.. _ciscosparkapi: https://pypi.python.org/pypi/ciscosparkapi
.. _PyYAML: https://pypi.python.org/pypi/PyYAML
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
