#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Commands"""

import argparse
import json
import logging
import logging.handlers
import signal
import sys
import time

import pymma
import pymma.beacon

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


def beacon_loop(igate, beacon_config):
    bcargs = {
        'lat': float(beacon_config['lat']),
        'lng': float(beacon_config['lng']),
        'callsign': igate.callsign,
        'table': beacon_config['table'],
        'symbol': beacon_config['symbol'],
        'comment': beacon_config['comment'],
        'ambiguity': beacon_config.get('ambiguity', 0),
    }

    bcargs_status = {
        'callsign': igate.callsign,
        'status': beacon_config['status'],
    }

    bcargs_weather = {
        'callsign': igate.callsign,
        'weather': beacon_config['weather'],
    }

    while 1:
        # Position
        frame = pymma.beacon.get_beacon_frame(**bcargs)
        if frame:
            igate.send(frame)

        # Status
        frame = pymma.beacon.get_status_frame(**bcargs_status)
        if frame:
            igate.send(frame)

        # Weather
        frame = pymma.beacon.get_weather_frame(**bcargs_weather)
        if frame:
            igate.send(frame)

        time.sleep(beacon_config['send_every'])


def cli():
    parser = argparse.ArgumentParser(description='PYMMA')

    parser.add_argument(
        '-c', dest='config',
        default='pymma.json',
        help='Use this config file')
    args = parser.parse_args()

    with open(args.config) as config_file:
        config = json.load(config_file)

    def mmcb(tnc2_frame):
        try:
            frame = pymma.APRSFrame()
            frame.import_tnc2(tnc2_frame)
            if bool(config.get('append_callsign')):
                frame.path.extend([u'qAR', config['callsign']])

            # Filter packets from TCP2RF gateways
            reject_paths = set(['TCPIP', 'TCPIP*', 'NOGATE', 'RFONLY'])
            # '}' is the Third-Party Data Type Identifier (used to encapsulate
            # pkgs) indicating traffic from the internet
            if (len(reject_paths.intersection(frame.path)) > 0 or
                    frame.payload.startswith('}')):
                print 'Rejected: %s' % frame.export(False)
            else:
                igate.send(frame)

        except pymma.InvalidFrame:
            print 'Invalid Frame Received.'
            pass

    print 'Starting PYMMA...'

    igate = pymma.IGate(
        config['callsign'],
        config['passcode'],
        config['gateways'],
        config.get('preferred_protocol', 'any')
    )

    multimon = pymma.Multimon(mmcb, config)

    def signal_handler(signal, frame):
        print 'Stopping PYMMA.'
        igate.exit()
        mm.exit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if config.get('beacon') is not None:
        beacon_loop(igate, config['beacon'])
    else:
        try:
            while igate._running and multimon._running:
                time.sleep(0.01)
        except KeyboardInterrupt:
            igate.exit()
            multimon._stop()
        finally:
            igate.exit()
            multimon._stop()


if __name__ == '__main__':
    cli()
