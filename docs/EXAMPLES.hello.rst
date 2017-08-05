Hello, World!
=============

Is this the most long-lasting contribution of Kernighan and Ritchie in their
famous book on the C language? Anyway, here we go with a quick start on
shellbot.

`View the source code of this example <https://github.com/bernard357/shellbot/blob/master/examples/hello.py>`_

How to execute a command?
--------------------------

Within shellbot, a command is simply a Python object with a member function
``execute()`` and an attribute ``keyword``. Maybe with a bare example this
will become much clearer::

    class Hello(Command):
        keyword = 'hello'

        def execute(self, bot, **kwargs):
            bot.say(u"Hello, World")

And that's it. if you pass an instance of ``Hello`` to the engine, it will
be invoked each time you send ``hello`` to the bot in the chat.

Got it. Can you provide a bit more?
-----------------------------------

Ok, here is the actual code featured in `the Hello World example <https://github.com/bernard357/shellbot/blob/master/examples/hello.py>`_::

    class Hello(Command):
        keyword = 'hello'
        information_message = u"Hello, World!"

        feedback_content = u"Hello, **{}**!"
        thanks_content = u"Thanks for the upload of `{}`"

        def execute(self, bot, arguments=None, attachment=None, url=None, **kwargs):

            bot.say(content=self.feedback_content.format(
                arguments if arguments else 'World'))

            if attachment:
                bot.say(content=self.thanks_content.format(attachment))

The signature of the ``execute()`` function show additional arguments for
commands that manage file uploads. Also, we provide to ``say()`` content
that is formatted in Markdown so that the rendering in chat is improved.

How to feed shellbot with commands?
-----------------------------------

By itself, shellbot provides only the ``help`` command. The command ``hello``
can be added to the engine during initialization::

  engine = Engine(command=Hello(), ...)

Of, course, a full set of commands can be provided to the engine. In the
:doc:`EXAMPLES.batman` example, we do::

  engine = Engine(commands=[Batman(), Batcave(), Batsignal(), Batsuicide()], ...)

How to change the banner?
-------------------------

The banner is sent to the chat area when the bot joins a new channel.
Shellbot support bare text, rich content, and even file uploads, altogether.
This can be changed by adjusting some environment variables, as shown below::

    os.environ['BOT_BANNER_TEXT'] = u"Type '@{} help' for more information"
    os.environ['BOT_BANNER_CONTENT'] = (u"Hello there! "
                                        u"Type ``@{} help`` at any time and  get "
                                        u"more information on available commands.")
    os.environ['BOT_BANNER_FILE'] = \
        "http://skinali.com.ua/img/gallery/19/thumbs/thumb_m_s_7369.jpg"

    engine.configure()

In this example environment variables are set within the python code itself,
yet for a regular application this should be done in a separate configuration
file.

How to select a chat platform?
------------------------------

The chat platform is selected during the initialization of the engine.
Here we put ``type='spark'`` to select Cisco Spark and that's it::

    engine = Engine(type='spark', command=Hello())

Ok, in addition to this code you also have to set some variables to make it
work, but this is regular configuration, done outside the code itself.

Does this manage multiple channels?
-----------------------------------

Shellbot powers as many channels as necessary from a single engine. In this
example a sample channel is created, yet you can invite the bot to any number
of other channels, or to your direct channel as well. Here you go::

    engine.bond(reset=True)  # create a group channel for this example
    engine.run()  # until Ctl-C
    engine.dispose()  # delete the initial group channel

Commands: hello, help
---------------------

The ``hello`` command is coming from this example itself, while ``help`` is
built in shellbot.

  hello
    response: Hello, World!

  hello Machine
    response: Hello, Machine!

  help
    response::

      Available commands:
      hello - Hello, World!
      help - Show commands and usage

  help hello
    response::

      hello - Hello, World!
      usage: hello

  help help
    response::

      help - Show commands and usage
      usage: help <command>

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
    python hello.py
