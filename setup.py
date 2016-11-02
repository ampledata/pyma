#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pymultimonaprs Package."""

import setuptools

__author__ = 'Dominik Heidler <dominik@heidler.eu>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


setuptools.setup(
    name='pymultimonaprs',
    version='3.0.0b1',
    license='GNU General Public License, Version 3',
    description='RF2APRS-IG Gateway',
    author='Greg Albrecht',
    author_email='oss@undef.net',
    url='http://github.com/ampledata/pymultimonaprs',
    packages=['pymultimonaprs'],
    entry_points={
        'console_scripts': [
            'pymultimonaprs = pymultimonaprs.cmd:main'
        ]
    },
    zip_safe=False,
    include_package_data=True
)
