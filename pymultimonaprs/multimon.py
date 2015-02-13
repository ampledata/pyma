#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pymultimonaprs Package."""

__author__ = 'Greg Albrecht W2GMD <gba@gregalbrecht.com>'
__copyright__ = 'Copyright 2015 OnBeep, Inc.'
__license__ = 'GNU General Public License, Version 3'


import logging
import logging.handlers
import threading
import subprocess
import re

import pymultimonaprs.constants


START_FRAME_REX = re.compile(r'^APRS: (.*)')
SAMPLE_RATE = 22050


class Multimon(object):

    logger = logging.getLogger(__name__)
    logger.setLevel(pymultimonaprs.constants.LOG_LEVEL)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(pymultimonaprs.constants.LOG_LEVEL)
    formatter = logging.Formatter(pymultimonaprs.constants.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False

    def __init__(self, frame_handler, config):
        self.frame_handler = frame_handler
        self.config = config
        self.subprocs = {}
        self._start()
        self._running = True
        self._worker = threading.Thread(target=self._mm_worker)
        self._worker.setDaemon(True)
        self._worker.start()

    def exit(self):
        self._running = False
        self._stop()

    def _start(self):
        if self.config['source'] == 'pulse':
            self.logger.debug('Using "pulse" as source.')

            proc_mm = subprocess.Popen(
                ['multimon-ng', '-a', 'AFSK1200', '-A'],
                stdout=subprocess.PIPE, stderr=open('/dev/null')
            )
        else:
            if self.config['source'] == 'rtl':
                self.logger.debug('Using "rtl" as source.')

                frequency = str(int(self.config['rtl']['freq'] * 1e6))
                sample_rate = str(SAMPLE_RATE)
                ppm = str(self.config['rtl']['ppm'])
                gain = str(self.config['rtl']['gain'])
                device_index = str(self.config['rtl'].get('device_index', 0))

                if self.config['rtl'].get('offset_tuning') is not None:
                    enable_option = 'offset'
                else:
                    enable_option = 'none'

                rtl_cmd = [
                    'rtl_fm',
                    '-f', frequency,
                    '-s', sample_rate,
                    '-p', ppm,
                    '-g', gain,
                    '-E', enable_option,
                    '-d', device_index,
                    '-'
                ]
                self.logger.debug('rtl_cmd=%s', rtl_cmd)

                proc_src = subprocess.Popen(
                    rtl_cmd, stdout=subprocess.PIPE, stderr=open('/dev/null'))
            elif self.config['source'] == 'alsa':
                self.logger.debug('Using "alsa" as source.')

                alsa_device = self.config['alsa']['device']
                sample_rate = str(SAMPLE_RATE)

                alsa_cmd = [
                    'arecord',
                    '-D', alsa_device,
                    '-r', sample_rate,
                    '-f', 'S16_LE',
                    '-t', 'raw',
                    '-c', '1',
                    '-'
                ]
                self.logger.debug('alsa_cmd=%s', alsa_cmd)

                proc_src = subprocess.Popen(
                    alsa_cmd, stdout=subprocess.PIPE, stderr=open('/dev/null'))

            mm_cmd = ['multimon-ng', '-a', 'AFSK1200', '-A', '-t', 'raw', '-']
            self.logger.debug('mm_cmd=%s', mm_cmd)

            proc_mm = subprocess.Popen(
                mm_cmd,
                stdin=proc_src.stdout,
                stdout=subprocess.PIPE,
                stderr=open('/dev/null'))

            self.subprocs['src'] = proc_src

        self.subprocs['mm'] = proc_mm

    def _stop(self):
        for name in ['mm', 'src']:
            try:
                proc = self.subprocs[name]
                proc.terminate()
            except:
                pass

    def _mm_worker(self):
        while self._running:
            line = self.subprocs['mm'].stdout.readline()
            line = line.strip()
            m = START_FRAME_REX.match(line)
            if m:
                tnc2_frame = m.group(1)
                self.frame_handler(tnc2_frame)
