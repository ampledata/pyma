#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Constats."""

import logging
import os
import re

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


if bool(os.environ.get('DEBUG')):
    LOG_LEVEL = logging.DEBUG
    logging.debug('Debugging Enabled via DEBUG Environment Variable.')
else:
    LOG_LEVEL = logging.INFO

LOG_FORMAT = logging.Formatter(
    '%(asctime)s pymma %(levelname)s %(name)s.%(funcName)s:%(lineno)d'
    ' - %(message)s')

START_FRAME_REX = re.compile(b'^APRS: (.*)')
SAMPLE_RATE = 22050

HEADER_REX = re.compile(
    b'^(?P<source>\w*(-\d{1,2})?)>(?P<dest>\w*(-\d{1,2})?),(?P<path>[^\s]*)')

# Filter packets from TCP2RF gateways
REJECT_PATHS = set(['TCPIP', 'TCPIP*', 'NOGATE', 'RFONLY'])

GPS_WARM_UP = 5

NMEA_PROPERTIES = [
    'timestamp',
    'lat',
    'latitude',
    'lat_dir',
    'lon',
    'longitude',
    'lon_dir',
    'gps_qual',
    'mode_indicator',
    'num_sats',
    'hdop',
    'altitude',
    'horizontal_dil',
    'altitude_units',
    'geo_sep',
    'geo_sep_units',
    'age_gps_data',
    'ref_station_id',
    'pos_fix_dim',
    'mode_fix_type',
    'mode',
    'pdop',
    'vdop',
    'fix'
]
