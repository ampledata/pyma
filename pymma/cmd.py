#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Commands"""

import argparse
import json
import Queue
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

    print 'Starting PYMMA...'

    frame_queue = Queue.Queue(maxsize=1)

    igate = pymma.IGate(
        frame_queue,
        config['callsign'],
        config['passcode'],
        config['gateways'],
        config.get('proto', 'any')
    )

    multimon = pymma.Multimon(frame_queue, config)

    if config.get('beacon'):
        beacon_loop(igate, config['beacon'])
    else:
        try:
            frame_queue.join()

            while igate._running and multimon._running:
                time.sleep(0.01)
        except KeyboardInterrupt:
            igate.exit()
            multimon.exit()
        finally:
            igate.exit()
            multimon.exit()


if __name__ == '__main__':
    cli()
