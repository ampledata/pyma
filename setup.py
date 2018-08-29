#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup for pymma.

Source:: https://github.com/ampledata/pymma
"""

import os
import setuptools  # type: ignore
import sys

__title__ = 'pymma'
__version__ = '2.0.0'
__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__license__ = 'GNU General Public License, Version 3'
__copyright__ = 'Copyright 2016 Dominik Heidler'


def publish():
    """Function for publishing package to pypi."""
    if sys.argv[-1] == 'publish':
        os.system('python setup.py sdist upload')
        sys.exit()


publish()


setuptools.setup(
    author='Greg Albrecht',
    author_email='oss@undef.net',
    description='Python Multimon APRS',
    entry_points={
        'console_scripts': [
            'pymma = pymma.cmd:cli'
        ]
    },
    include_package_data=True,
    install_requires=[
        'aprslib',
        'requests',
        'pynmea2 >= 1.4.2',
        'pyserial >= 2.7'
    ],
    license=open('LICENSE').read(),
    long_description=open('README.rst').read(),
    name='pymma',
    package_data={'': ['LICENSE']},
    package_dir={'pymma': 'pymma'},
    packages=['pymma'],
    url='http://github.com/ampledata/pymma',
    version=__version__,
    zip_safe=False
)
