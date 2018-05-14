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

    igate = pymma.IGate(frame_queue, config)
    multimon = pymma.Multimon(frame_queue, config)

    threads = [igate, multimon]

    if config.get('beacon'):
        beacon = pymma.Beacon(igate, config)
        threads.append(beacon)

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
