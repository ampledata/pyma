#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Package."""

import setuptools

__author__ = 'Greg Albrecht <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


setuptools.setup(
    name='pymma',
    version='0.0.1b1',
    license='GNU General Public License, Version 3',
    description='Python APRS Gateway',
    author='Greg Albrecht',
    author_email='oss@undef.net',
    url='http://github.com/ampledata/pymma',
    packages=['pymma'],
    entry_points={
        'console_scripts': [
            'pymma = pymma.cmd:cli'
        ]
    },
    zip_safe=False,
    include_package_data=True
)
