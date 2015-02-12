#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pymultimonaprs Package."""

__author__ = 'Greg Albrecht W2GMD <gba@gregalbrecht.com>'
__copyright__ = 'Copyright 2015 OnBeep, Inc.'
__license__ = 'GNU General Public License, Version 3'


import argparse
import json
import logging
import logging.handlers
import signal
import sys
import threading
import time


from pymultimonaprs.multimon import Multimon
from pymultimonaprs import beacon
from pymultimonaprs.gate import IGate
from pymultimonaprs.frame import APRSFrame, InvalidFrame


def main():
    parser = argparse.ArgumentParser(description='pymultimonaprs.')
    parser.add_argument('-c', dest='config', default='pymultimonaprs.json', help='Use this config file')
    parser.add_argument('--syslog', action='store_true', help='Log to syslog')
    parser.add_argument('-v', '--verbose', action='store_true', help='Log all traffic - including beacon')
    args = parser.parse_args()

    with open(args.config) as config_file:
        config = json.load(config_file)

    logger = logging.getLogger('pymultimonaprs')
    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(loglevel)

    if args.syslog:
        loghandler = logging.handlers.SysLogHandler(address = '/dev/log')
        formater = logging.Formatter('pymultimonaprs: %(message)s')
        loghandler.setFormatter(formater)
    else:
        loghandler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)+8s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        loghandler.setFormatter(formatter)
    logger.addHandler(loghandler)


    def mmcb(tnc2_frame):
        try:
            frame = APRSFrame()
            frame.import_tnc2(tnc2_frame)
            if config['append_callsign']:
                frame.path.extend([u'qAR', config['callsign']])
            ig.send(frame)
        except InvalidFrame:
            logger.info('Invalid Frame Received.')
            pass

    def bc():
        bcargs = {
            'lat': config['beacon']['lat'],
            'lng': config['beacon']['lng'],
            'callsign': config['callsign'],
            'table': config['beacon']['table'],
            'symbol': config['beacon']['symbol'],
            'comment': config['beacon']['comment'],
            'ambiguity': config['beacon'].get('ambiguity', 0),
        }
        bcargs_status = {
            'callsign': config['callsign'],
            'status': config['beacon']['status'],
        }
        bcargs_weather = {
            'callsign': config['callsign'],
            'weather': config['beacon']['weather'],
        }
        while 1:
            # Position
            frame = beacon.get_beacon_frame(**bcargs)
            if frame:
                ig.send(frame)

            # Status
            frame = beacon.get_status_frame(**bcargs_status)
            if frame:
                ig.send(frame)

            # Weather
            frame = beacon.get_weather_frame(**bcargs_weather)
            if frame:
                ig.send(frame)

            sleep(config['beacon']['send_every'])

    logger.info('Starting pymultimonaprs')

    ig = IGate(config['callsign'], config['passcode'], config['gateway'])
    mm = Multimon(mmcb,config)

    def signal_handler(signal, frame):
        logger.info('Stopping pymultimonaprs')
        ig.exit()
        mm.exit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start beacon in main thread
    if config.get('beacon'):
        bc()


if __name__ == '__main__':
    main()
