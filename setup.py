#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os.path import join as pjoin
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# get requirements from separate files
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('requirements_test.txt') as f:
    test_requirements = f.read().splitlines()

# get version from package itself
version = '0.0.0'
with open('shellbot/__init__.py') as f:
    lines = f.read().splitlines()
    for line in lines:
        match = re.match(r"__version__ = '(.*?)'", line)
        if match:
            version = match.group(1)
            break

# get description from README.rst
def get_long_description():
    description = ''
    with open('README.rst') as stream:
        description = stream.read()
    return description

setup(
    name='shellbot',
    version=version,
    description="A bot that is also a responsive shell",
    long_description=get_long_description(),
    author="Bernard Paques",
    author_email='bernard.paques@gmail.com',
    url='https://github.com/bernard357/shellbot',
    packages=['shellbot'],
    package_dir={'shellbot': 'shellbot'},
    include_package_data=True,
    install_requires=requirements,
    license='Apache License (2.0)',
    zip_safe=False,
    keywords='bot, shell',
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: No Input/Output (Daemon)',
        'Framework :: Bottle',
        'Framework :: Paste',
        'Framework :: Sphinx',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Conferencing',
        'Topic :: Communications :: Internet Phone',
        'Topic :: Communications :: Telephony',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Shells',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
