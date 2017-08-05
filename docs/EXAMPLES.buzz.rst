Fly with Buzz -- "To infinity and beyond"
=========================================

In this example we deal with commands that take significant
time to execute. How to run long-lasting transactions in the background, so
that the bot stays responsive?

`View the source code of this example <https://github.com/bernard357/shellbot/blob/master/examples/buzz.py>`_

Buzz is flying from Earth to some planets and come back. Obviously,
this is the kind of activity that can take ages, yet here each mission
lasts about 30 seconds.

Ok. So, when I type ``explore Uranus`` in the chat box, do I have to
wait for 30 seconds before the next command is considered? Hopefully not!

How to execute commands asynchronously?
---------------------------------------

The two commands ``explore`` and ``blast`` are non-interactive. This means
that they are pushed to a pipeline for background execution.
With this concept, you can get a dialog similar to the following::

    > buzz explore Mercury
    Ok, I am working on it
    #1 - Departing to Mercury
    > buzz blast Neptune
    Ok, will work on it as soon as possible
    #1 - Approaching Mercury
    #1 - Landed on Mercury
    > buzz planets
    Available destinations:
    - Venus
    - Moon

    ...

In other terms, the bot is always responsive, whatever is executing in the
background. Also, non-interactive commands are executed in the exact
sequence of their submission.

These concepts are implemented with instances of ``Rocket`` that are attached
to bots (`Rocket source code <https://github.com/bernard357/shellbot/blob/master/examples/planets/rocket.py>`_).
Every rocket has a queue that receives commands submitted
in the chat box. And of course, every rocket is running a separate process
to pick up new missions and to execute them.

How to attach a rocket and make it fly, for every bot?
------------------------------------------------------

Since the objective is that each bot has its own rocket attached, we provide
with a custom driver that does exactly this::

    class FlyingBot(ShellBot):  # add a rocket to each bot
        def on_init(self):
            self.rocket = Rocket(self)
            self.rocket.start()

Then the engine is instructed to use this custom driver instead of the
regular one::

    engine = Engine(driver=FlyingBot, ...)

With this way of working, each time the bot is invited to a channel (direct or
group), a new rocket is instantiated and ready to go.

How can a command interact with the rocket?
-------------------------------------------

The command delegates a new mission with a simple function call, like for
example in the command ``explore``::

    class Explore(Command):
        keyword = u'explore'
        information_message = u'Explore a planet and come back'
        usage_message = u'explore <destination>'

        def execute(self, bot, arguments=None, **kwargs):
            """
            Explores a planet and comes back
            """

            if arguments in (None, ''):
                bot.say(u"usage: {}".format(self.usage_message))
                return

            bot.rocket.go('explore', arguments)

On rocket side, the mission is pushed to a queue for later processing::

    def go(self, action, planet):
        """Engages a new mission"""

        self.inbox.put((action, planet))

Within the rocket instance, a process is continuously monitoring the
``inbox`` queue to pick up new missions and to execute them, one at a time.

How to store data separately for each bot?
------------------------------------------

With shellbot, each bot is coming with its own data store, that is distinct
from data stores of other bots.
Content of the bot store can be statically initialized by the engine itself, if
settings starting with the label ``bot.store`` are provided. This mechanism is
used in this example for listing available planets::

    engine.set(
        'bot.store.planets',
        ['Mercury', 'Venus', 'Moon', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'])

The function ``bot.recall()`` can then be used to retrieve the list of
planets. This is exactly what is done for the command ``planets``::

    class Planets(Command):
        keyword = u'planets'
        information_message = u'List reachable planets'

        list_header = u"Available destinations:"

        def execute(self, bot, arguments=None, **kwargs):
            """
            Displays the list of available planets
            """

            items = bot.recall('planets', [])
            if len(items):
                bot.say(self.list_header
                        + '\n- ' + '\n- '.join(items))
            else:
                bot.say(u"Nowhere to go right now.")


When a planet has been blasted, it is removed from the data store with
code similar to this::

    items = self.bot.recall('planets', [])
    items.remove(planet)
    self.bot.remember('planets', items)

Keep in mind that the list of available planets evolve over time,
since some of them can be nuked by end users. So, if Mercury is blasted in one
channel, and Neptune in another channel, there is a need for independent
management of planets across bots. This is exactly what ``bot.remember()`` and
``bot.recall()`` provide, hopefully.

Commands: planets, explore, blast
---------------------------------

  planets
    provides a list of available destinations

  explore <planet>
    you then track in real-time the progress of the mission

  blast <planet>
    similar to exploration, except that the planet is nuked


How to run this example?
------------------------

To run this script you have to provide a custom configuration, or set
environment variables instead:

- ``CHANNEL_DEFAULT_PARTICIPANTS`` - Mention at least your e-mail address
- ``CISCO_SPARK_BOT_TOKEN`` - Received from Cisco Spark on bot registration
- ``SERVER_URL`` - Public link used by Cisco Spark to reach your server

The token is specific to your run-time, please visit Cisco Spark for
Developers to get more details:

    https://developer.ciscospark.com/

For example, if you run this script under Linux or macOs with support from
ngrok for exposing services to the Internet::

    export CHANNEL_DEFAULT_PARTICIPANTS="alice@acme.com"
    export CISCO_SPARK_BOT_TOKEN="<token id from Cisco Spark for Developers>"
    export SERVER_URL="http://1a107f21.ngrok.io"
    python buzz.py
