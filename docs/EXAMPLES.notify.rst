Notify
======

In this example we use the bot only for easy notifications to a space.
There is no command in the shell at all, and the bot is not even started.

`View the source code of this example <https://github.com/bernard357/shellbot/blob/master/examples/notify.py>`_

How to create a bot and configure it in one line?
-------------------------------------------------

The simplest approach is to set environment variables and then to create the
bot. This can be done externally, before running the program, for secret
variables such as the Cisco Spark token (see below). Or variables can be set
directly from within the script itself, as ``CHAT_ROOM_TITLE`` in this example.

How to create or to delete a channel?
-------------------------------------

When you access a bot for the first time it is created automatically in the
back-end platform. From a software perspective, call ``engine.get_bot()`` and
this will give you a bot instance.

The bot itself can be used when you have to delete a channel, with a call of
``bot.dispose()``.

How to post a notification?
---------------------------

Use ``bot.say()`` on the bot instance. Messages posted can feature bare or rich
text, and you can also upload an image or a document file.

Why do we not start the bot?
--------------------------------------------

There is no call to ``bot.run()`` here because there is no need for an
active shell. The program updates a channel, however is not interactive
and cannot answer messages send to it. Of course, it is easy to implement a
couple of commands at some point so that you evolve towards a responsive bot.

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
    python notify.py
