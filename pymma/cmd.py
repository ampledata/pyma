#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Commands"""

import argparse
import json
import queue
import time

import pymma

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


def cli():
    parser = argparse.ArgumentParser(description='PYMMA')

    parser.add_argument(
        '-c', dest='config',
        default='pymma.json',
        help='Use this config file')
    args = parser.parse_args()

    with open(args.config) as config_file:
        config = json.load(config_file)

    print('Starting PYMMA...')

    threads: list = []
    frame_queue: queue.Queue = queue.Queue()

    igate_thread = pymma.IGateThread(frame_queue, config)
    multimon_thread = pymma.MultimonThread(frame_queue, config)

    threads = [igate_thread, multimon_thread]

    location_config: dict = {}
    beacon_config = config.get('beacon')
    if beacon_config:
        location_config = beacon_config.get('location')

    if location_config.get('static'):
        beacon_thread = pymma.StaticBeaconThread(igate_thread, config)
        threads.append(beacon_thread)
    elif location_config.get('gps'):
        gps_config = location_config.get('gps')
        gps_p = pymma.SerialGPSPoller(gps_config['port'], gps_config['speed'])
        threads.append(gps_p)

        gps_p.start()

        time.sleep(pymma.GPS_WARM_UP)

        beacon_thread = pymma.GPSBeaconThread(igate_thread, config)
        threads.append(beacon_thread)

    try:
        [thr.start() for thr in threads]

        frame_queue.join()

        while all([thr.is_alive() for thr in threads]):
            time.sleep(0.01)
    except KeyboardInterrupt:
        [thr.stop() for thr in threads]

    finally:
        [thr.stop() for thr in threads]


if __name__ == '__main__':
    cli()
