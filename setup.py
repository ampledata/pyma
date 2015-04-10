#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pymultimonaprs Package."""

__author__ = 'Greg Albrecht W2GMD <gba@gregalbrecht.com>'
__copyright__ = 'Copyright 2015 Orion Labs'
__license__ = 'GNU General Public License, Version 3'


import setuptools


setuptools.setup(
    name='pymultimonaprs',
    version='2.0.0',
    license='GNU General Public License, Version 3',
    description='RF2APRS-IG Gateway',
    author='Greg Albrecht',
    author_email='gba@gregalbrecht.com',
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
