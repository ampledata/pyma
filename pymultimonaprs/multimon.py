#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pymultimonaprs Package."""

import logging
import logging.handlers
import threading
import subprocess

import pymultimonaprs.constants

__author__ = 'Dominik Heidler <dominik@heidler.eu>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


class Multimon(object):

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymultimonaprs.constants.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymultimonaprs.constants.LOG_LEVEL)
        _console_handler.setFormatter(pymultimonaprs.constants.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

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
            self._logger.debug('source=%s', self.config['source'])

            multimon_cmd = ['multimon-ng', '-a', 'AFSK1200', '-A']
            self._logger.debug('multimon_cmd=%s', multimon_cmd)

            proc_mm = subprocess.Popen(
                multimon_cmd,
                stdout=subprocess.PIPE,
                stderr=open('/dev/null')
            )
        else:
            if self.config['source'] == 'rtl':
                self._logger.debug('source=%s', self.config['source'])

                sample_rate = str(pymultimonaprs.constants.SAMPLE_RATE)

                # Allow use of 'rx_fm' for Soapy/hackrf
                rf_cmd = self.config['rtl'].get('command', 'rtl_fm')

                frequency = str(int(self.config['rtl']['freq'] * 1e6))
                ppm = str(self.config['rtl']['ppm'])
                gain = str(self.config['rtl']['gain'])

                device_index = int(self.config['rtl'].get('device_index', 0))

                if self.config['rtl'].get('offset_tuning') is not None:
                    enable_option = 'offset'
                else:
                    enable_option = 'none'

                rtl_args = [
                    '-f', frequency,
                    '-s', sample_rate,
                    '-p', ppm,
                    '-g', gain,
                    '-E', enable_option
                ]

                # 'rx_fm' support.
                if device_index >= 0:
                    rtl_args.extend('-d', str(device_index))

                rtl_cmd = [rf_cmd].extend(rtl_args).extend(['-'])

                self._logger.debug('rtl_cmd=%s', rtl_cmd)

                proc_src = subprocess.Popen(
                    rtl_cmd,
                    stdout=subprocess.PIPE,
                    stderr=open('/dev/null')
                )

            elif self.config['source'] == 'alsa':
                self._logger.debug('source=%s', self.config['source'])

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
                self._logger.debug('alsa_cmd=%s', alsa_cmd)

                proc_src = subprocess.Popen(
                    alsa_cmd,
                    stdout=subprocess.PIPE,
                    stderr=open('/dev/null')
                )

            mm_cmd = ['multimon-ng', '-a', 'AFSK1200', '-A', '-t', 'raw', '-']
            self._logger.debug('mm_cmd=%s', mm_cmd)

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
            m = pymultimonaprs.constants.START_FRAME_REX.match(line)
            if m:
                tnc2_frame = m.group(1)
                self.frame_handler(tnc2_frame)
