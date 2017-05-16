#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Constats."""

import logging
import os
import re

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'



if bool(os.environ.get('DEBUG_PYMMA')) or bool(os.environ.get('DEBUG_ALL')):
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

LOG_FORMAT = logging.Formatter(
    '%(asctime)s pymma %(levelname)s %(name)s.%(funcName)s:%(lineno)d'
    ' - %(message)s')

START_FRAME_REX = re.compile(r'^APRS: (.*)')
SAMPLE_RATE = 22050

HEADER_REX = re.compile(
    r'^(?P<source>\w*(-\d{1,2})?)>(?P<dest>\w*(-\d{1,2})?),(?P<path>[^\s]*)')

# Filter packets from TCP2RF gateways
REJECT_PATHS = set(['TCPIP', 'TCPIP*', 'NOGATE', 'RFONLY'])
