===================================
Shellbot: Python Chat Bot Framework
===================================

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


Fast, simple and lightweight micro bot framework for Python. It is distributed
as a single package and has very few dependencies other than the
`Python Standard Library <http://docs.python.org/library/>`_. Shellbot supports
Python 3 and Python 2.7. Test coverage exceeds 90%.

* **Channels:** a single bot can access jointly group and direct channels
* **Commands:** routing from chat box to function calls made easy, including support of file uploads
* **State machines:** powerful and pythonic way to bring intelligence to your bot
* **Stores:** each bot has a dedicated data store
* **Utilities:** convenient configuration-driven approach, chat audit, and more
* **Platforms:** Cisco Spark, local disconnected mode for tests -- looking for more

The Batman example
------------------

.. code-block:: python

      import os
      import time

      from shellbot import Engine, Context, Command
      Context.set_logger()


      class Batman(Command):  # a command that displays static text
          keyword = 'whoareyou'
          information_message = u"I'm Batman!"


      class Batcave(Command):  # a command that reflects input from the end user
          keyword = 'cave'
          information_message = u"The Batcave is silent..."

          def execute(self, bot, arguments=None, **kwargs):
              if arguments:
                  bot.say(u"The Batcave echoes, '{0}'".format(arguments))
              else:
                  bot.say(self.information_message)


      class Batsignal(Command):  # a command that uploads a file/link
          keyword = 'signal'
          information_message = u"NANA NANA NANA NANA"
          information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

          def execute(self, bot, arguments=None, **kwargs):
              bot.say(self.information_message,
                      file=self.information_file)


      class Batsuicide(Command):  # a command only for group channels
          keyword = 'suicide'
          information_message = u"Go back to Hell"
          in_direct = False

          def execute(self, bot, arguments=None, **kwargs):
              bot.say(self.information_message)
              bot.dispose()


      engine = Engine(  # use Cisco Spark and load shell commands
          type='spark',
          commands=[Batman(), Batcave(), Batsignal(), Batsuicide()])

      os.environ['BOT_ON_ENTER'] = 'You can now chat with Batman'
      os.environ['BOT_ON_EXIT'] = 'Batman is now quitting the room, bye'
      os.environ['CHAT_ROOM_TITLE'] = 'Chat with Batman'
      engine.configure()  # ensure that all components are ready

      engine.bond(reset=True)  # create a group channel for this example
      engine.run()  # until Ctl-C
      engine.dispose()  # delete the initial group channel

Are you looking for practical documentation?
:doc:`EXAMPLES`

Quick installation
------------------

To install the shellbot package, type::

    $ pip install shellbot

Or, if you prefer to download the full project including examples and documentation,
and install it, do the following::

    $ git clone https://github.com/bernard357/shellbot.git
    $ cd shellbot
    $ pip install -e .


Where do you want to start?
---------------------------

* Documentation: `Shellbot at ReadTheDocs`_
* Python package: `Shellbot at PyPi`_
* Source code: `Shellbot at GitHub`_
* Free software: `Apache License (2.0)`_


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
