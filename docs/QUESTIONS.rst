Frequently asked questions
##########################

This page is updated with questions frequently asked to the team.

.. contents:: :depth: 3

About project governance
========================

Where is this project coming from?
----------------------------------

The shellbot project started as an initiative from some colleagues within Dimension Data.
We saw a need for a simple, rock-solid and fast package that would allow us to
support upcoming client projects.

Is this software available to anyone?
-------------------------------------

Yes. The software and the documentation have been open-sourced from the outset, so that it can be useful to the global community of bot practioners. The shellbot project is based on the `Apache License`_.

Do you accept contributions to this project?
--------------------------------------------

Yes. There are multiple ways for end-users and for non-developers to contribute to this project. For example, if you hit an issue, please report it at GitHub. This is where we track issues and report on corrective actions. More information at :doc:`CONTRIBUTING`

And if you know `how to clone a GitHub project`_, we are happy to consider `pull requests`_ with your modifications. This is the best approach to submit additional examples, or updates of the documentation, or evolutions of the python code itself.

How do you structure version numbering?
---------------------------------------

We put the year, month, and date of the release. So for example version 17.5.7
has been generated on May-5th, 2017.

About shellbot design
=====================

What is needed to run shellbot?
-------------------------------

Shellbot requires essentially a recent `python`_ interpreter. Both versions 2.x and 3.x are accepted. We are aiming
to limit dependencies to the very minimum, and to leverage the standard python library as much as possible. Of course,
we use some external library related to Cisco Spark. For development and tests, even a small computer can be used,
providing that it is connected to the Internet. This can be your own workstation or even a small computer like a Raspberry Pi. Or any general-purpose computer, really. And, of course, it can be a virtual server running in the cloud.

What systems are compatible with shellbot?
-------------------------------------------

Currently, shellbot can interact with Cisco Spark. Our mid-term objective is that it can interface with multiple systems. The architecture is open, so that it can be extended quite easily. We are looking for the addition of Slack, Gitter and Microsoft Teams. If you are interested, or have other ideas, please have a look at :doc:`CONTRIBUTING`

About shellbot deployment
=========================

How to install shellbot?
---------------------------------------------------

Shellbot uses the standard approach for the distribution of python packages
via PyPi. In other terms::

    pip install shellbot


Check :doc:`SETUP` for more details.

Is it required to know python?
------------------------------

Yes. Shellbot is a powerful framework with a simple interface. You can start
small and expand progressively.

How to run shellbot interactively?
----------------------------------

Shellbot is a framework, not a end product on its own. If you get a local copy
of the project from GitHub, then go to directory ``examples`` and run direclty
one of the python script there.

For example to run the Buzz example::

    $ python buzz.py

Break the infinite pumping loop if needed with the keystroke `Ctrl-X`.

My question has not been addressed here. Where to find more support?
====================================================================

Please `raise an issue at the GitHub project page`_ and get support from the project team.


.. _`Apache License`: https://www.apache.org/licenses/LICENSE-2.0
.. _`how to clone a GitHub project`: https://help.github.com/articles/cloning-a-repository/
.. _`pull requests`: https://help.github.com/articles/about-pull-requests/
.. _`python`: https://www.python.org
.. _`raise an issue at the GitHub project page`: https://github.com/bernard357/mcp-watch/issues