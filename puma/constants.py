#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Constants for pymultimonaprs Module.
"""

import logging
import re

__author__ = 'Dominik Heidler <dominik@heidler.eu>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


LOG_LEVEL = logging.DEBUG
LOG_FORMAT = logging.Formatter(
    '%(asctime)s pymultimonaprs %(levelname)s %(name)s.%(funcName)s:%(lineno)d'
    ' - %(message)s')

START_FRAME_REX = re.compile(r'^APRS: (.*)')
SAMPLE_RATE = 22050
