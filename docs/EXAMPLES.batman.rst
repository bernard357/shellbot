Chat with Batman
================

In this example the bot pretends to be Batman, and supports some commands
that are making sense in this context.

`View the source code of this example <https://github.com/bernard357/shellbot/blob/master/examples/batman.py>`_

How to build a dynamic response?
--------------------------------

Look at the command ``cave``, where the message pushed to the chat channel
depends on the input received. This is done with regular python code in the
member function ``execute()``::

    class Batcave(Command):
        keyword = 'cave'
        information_message = u"The Batcave is silent..."

        def execute(self, bot, arguments=None, **kwargs):
            if arguments:
                bot.say(u"The Batcave echoes, '{0}'".format(arguments))
            else:
                bot.say(self.information_message)

Of course, for your own application, it is likely that tests would be a bit
more complicated. For example, you could check data from the bot store with
``bot.recall()``, or specific settings of the engine with ``bot.engine.get()``,
or use a member attribute of the command itself. This is demonstrated in
other examples.

How to upload files?
--------------------

The command ``signal`` demonstrates how to attach a link or a file to a
message::

    class Batsignal(Command):
        keyword = 'signal'
        information_message = u"NANA NANA NANA NANA"
        information_file = "https://upload.wikimedia.org/wikipedia/en/c/c6/Bat-signal_1989_film.jpg"

        def execute(self, bot, arguments=None, **kwargs):
            bot.say(self.information_message,
                    file=self.information_file)

Here we use some public image, yet the same would work for the upload
of a local file::

    bot.say('my report', file='./shared/reports/August-2017.xls')

In a nutshell: with shellbot, files are transmitted along the regular
function ``say()``.

What about commands that do not apply to direct channels?
---------------------------------------------------------

When you have this requirement, set the command attribute ``in_direct`` to
``False``. In this example, the bot is not entitled to delete a private
channel. So we disable the command ``suicide`` from direct channels::

    class Batsuicide(Command):
        keyword = 'suicide'
        information_message = u"Go back to Hell"
        in_direct = False

        def execute(self, bot, arguments=None, **kwargs):
            bot.say(self.information_message)
            bot.dispose()

If you use the command ``help`` both in group channel and in direct channel,
you will see that the list of available commands is different.

How to load multiple commands?
------------------------------

Since each command is a separate object, you can add them as a list bundle
to the engine::

    engine = Engine(
        type='spark',
        commands=[Batman(), Batcave(), Batsignal(), Batsuicide()])

In this example we create an instance from each class, and put that in a list
for the engine.

BatCommands: whoareyou, cave, signal, suicide
---------------------------------------------

These are a bit more sophisticated than for the :doc:`EXAMPLES.hello` example,
but not much.

  whoareyou
    response: I'm Batman!

  cave
    response: The Batcave is silent...

  cave give me some echo
    response: The Batcave echoes, 'give me some echo'

  signal
    response: NANA NANA NANA NANA

    This command also uploads an image to the chat channel.

  suicide
    response: Going back to Hell

    The command also deletes the channel where it was executed.
    It is available only within group channels, and not in direct channels.

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
    python batman.py


Credit: https://developer.ciscospark.com/blog/blog-details-8110.html
