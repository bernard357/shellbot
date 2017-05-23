How to contribute to Shellbot?
##############################

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

    "80% of success is just showing up." - Woody Allen

Contributing to open source for the first time can be scary and a little overwhelming.
This project is like the others. It needs help and that help can mean using it, sharing the information,
supporting people, whatever. The thing that folks forget about open source is that it's most volunteers who are doing it for the love of it. They show up.

.. contents::

You are not a developer? We are glad that you are involved.
===========================================================

We want you to feel as comfortable as possible with this project, whatever your skills are.
Here are some ways to contribute:

* use it for yourself
* communicate about the project
* submit feedback
* report a bug
* write or fix documentation
* fix a bug or an issue
* implement some feature

How to use shellbot for yourself?
---------------------------------

Initially the shellbot project has been initiated so that as many
IT professionals as possible can develop bots in python. Look at examples
coming with the framework and see how they can accelerate your own projects.
Duplicate one example for yourself, expand it and enjoy!

How to communicate about the shellbot project?
----------------------------------------------

If you believe that the project can help other persons, for whatever reason,
just be social about it. Use Facebook, LinkedIn, Twitter, or any other tool
that are used by people you dare. Lead them to build a bot with shellbot.

How to submit feedback?
-----------------------

The best way to send feedback, positive or negative, is to file an issue.
At first sight it may seems strange to mix feedback with issues. In practice this
is working smoothly because there is a single place for asynchronous interactions
across the project community.

`Provide feedback right now`_

Your use case may be new, and therefore interesting to us. Or you may raise the hand
and explain your own user experience, bad or good. Ask a question if something
is not clear. If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

How to report a bug?
--------------------

Have you identified some bug? This is great! There is a single place for
all bugs related to this project:

`Shellbot bugs and issues`_

This is where issues are documented and discussed before they are fixed by the
community. Each time you report a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

How to improve the documentation?
---------------------------------

The project could always use more documentation, for sure.
Currently documentation is generated automatically from GitHub updates
and made available at ReadTheDocs.

`Shellbot primary documentation`_

Documentation files in `reST format`_ (i.e., text files with an extension ``.rst``)
sit in the ``docs`` directory. Images are put in ``docs\_static``. Therefore,
updating the documentation is as simple as changing any project source file.

So if you already used a text editor, and made some screenshots, please consider
to improve project documentation.

For example, here are the typical steps required for the addition of a new tutorial page:

1. From `the project page at GitHub`_, you can `fork it`_ so that you have your own project space.
   If you do not have a GitHub account, please create one. This is provided for free, and will
   make you a proud member of a global community that matters.

2. Clone the forked project to your workstation so that you get a copy of all files there.
   `GitHub Desktop`_ is recommended across all platforms it supports.

3. Open a text editor and write some text in `reST format`_. Then save it
   to a new document, e.g., ``docs\tutorial01.rst``

4. Make some screen shots or select some pictures that will be displayed
   within the document. Put all of them in ``docs\_static``.

5. Commit changes and push them back to GitHub. On GitHub Desktop this is
   as simple as clicking on the Sync button.

6. Visit the forked project page at GitHub and navigate to the new documentation
   page. The reST will be turned automatically to a web page, so that you can
   check everything. Go back to step 4 and iterate as much as needed.

7. When you are really satisfied by your work, then submit it to the community
   with `a Pull Request`_. Again, in GitHub Desktop this is a simple click on a button.

8. All `Pull Requests are listed from the original project page`_
   so you can monitor what the community is doing with them, and jump in anytime.

9. When your Pull Request is integrated, then your contribution is
   becoming an integral part of the project, and you become an official
   contributor. Thank you!

How to fix a bug?
-----------------

Look through `the GitHub issues`_ for bugs.
Anything tagged with "bug" is open to whoever wants to implement it.

How to implement new features?
------------------------------

Look through `the GitHub issues`_ for features.
Anything tagged with "enhancement" is open to whoever wants to implement it.

Ready to contribute? Here's how to set up Shellbot for local development
========================================================================

1. Fork the `shellbot` repo on `GitHub`_. If you do not have an account there
   yet, you have to create one, really. This is provided for free, and will
   make you a proud member of a global community that matters. Once you have
   authenticated, visit the `Shellbot repository at GitHub`_ and click
   on the `Fork` link.

2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/shellbot.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper
   installed, this is how you set up your fork for local development::

    $ mkvirtualenv shellbot
    $ cd shellbot/
    $ pip install -e .

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the tests::

    $ make lint
    $ make test
    $ make coverage

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Some guidelines for your next Pull Request
==========================================

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in ``README.rst``.

3. Check `Shellbot continuous integration at Travis CI`_
   and make sure that the tests pass there.

.. _`a Pull Request`: https://help.github.com/articles/about-pull-requests/
.. _`Pull Requests are listed from the original project page`: https://github.com/bernard357/shellbot/pulls
.. _`the GitHub issues`: https://github.com/bernard357/shellbot/issues
.. _`Shellbot primary documentation`: http://shellbot-for-cisco-spark.readthedocs.io/en/latest/
.. _`GitHub`: https://github.com/
.. _`Shellbot repository at GitHub`: https://github.com/bernard357/shellbot
.. _`Shellbot issues at GitHub`: https://github.com/bernard357/shellbot/issues
.. _`Provide feedback right now`: https://github.com/bernard357/shellbot/issues
.. _`Shellbot bugs and issues`: https://github.com/bernard357/shellbot/issues
.. _`Shellbot continuous integration at Travis CI`: https://travis-ci.org/bernard357/shellbot
.. _`the project page at GitHub`: https://github.com/bernard357/shellbot
.. _`fork it`: https://help.github.com/articles/fork-a-repo/
.. _`GitHub Desktop`: https://desktop.github.com/
.. _`reST format`: http://www.sphinx-doc.org/en/stable/rest.html
