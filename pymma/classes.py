#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Classes."""

import errno
import itertools
import logging
import logging.handlers
import pkg_resources
import Queue
import random
import re
import socket
import subprocess
import threading
import time

import pymma.constants

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


HEADER_REX = re.compile(
    r'^(?P<source>\w*(-\d{1,2})?)>(?P<dest>\w*(-\d{1,2})?),(?P<path>[^\s]*)')


class InvalidFrame(Exception):
    pass


class APRSFrame(object):

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.constants.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.constants.LOG_LEVEL)
        _console_handler.setFormatter(pymma.constants.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self):
        self.source = None
        self.dest = None
        self.path = []
        self.payload = unicode()

    def import_tnc2(self, tnc2_frame, decode=True):
        if decode:
            tnc2_frame = tnc2_frame.decode('ISO-8859-1')

        tnc2_frame = tnc2_frame.replace('\r', '')
        header, payload = tnc2_frame.split(':', 1)
        header = header.strip()
        payload = payload.strip()

        try:
            res = HEADER_REX.match(header).groupdict()
            self.source = res['source']
            self.dest = res['dest']
            self.path = res['path'].split(',')
        except:
            raise InvalidFrame()

        self.payload = payload

    def export(self, encode=True):
        tnc2 = "%s>%s,%s:%s" % (
            self.source, self.dest, ','.join(self.path), self.payload)
        if len(tnc2) > 510:
            tnc2 = tnc2[:510]
        if encode:
            tnc2 = tnc2.encode('ISO-8859-1')
        return tnc2


class IGate(object):

    """PYMMA IGate Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.constants.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.constants.LOG_LEVEL)
        _console_handler.setFormatter(pymma.constants.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, callsign, passcode, gateways, preferred_protocol):
        self.callsign = callsign
        self.passcode = passcode
        self.gateways = itertools.cycle(gateways)
        self.preferred_protocol = preferred_protocol

        self.socket = None
        self.server = ''
        self.port = 0
        self.connected = False

        self._sending_queue = Queue.Queue(maxsize=1)
        self._connect()

        self._running = True

        self._worker = threading.Thread(target=self._socket_worker)
        self._worker.setDaemon(True)
        self._worker.start()

    def exit(self):
        self._running = False
        self._disconnect()

    def _connect(self):
        while not self.connected:
            try:
                # Connect
                gateway = next(self.gateways)
                self.server, self.port = gateway.split(':')
                self.port = int(self.port)

                if self.preferred_protocol == 'ipv6':
                    addrinfo = socket.getaddrinfo(
                        self.server, self.port, socket.AF_INET6)
                elif self.preferred_protocol == 'ipv4':
                    addrinfo = socket.getaddrinfo(
                        self.server, self.port, socket.AF_INET)
                else:
                    addrinfo = socket.getaddrinfo(self.server, self.port)

                self.socket = socket.socket(*addrinfo[0][0:3])

                self._logger.info(
                    "Connecting to %s:%i" % (addrinfo[0][4][0], self.port))

                self.socket.connect(addrinfo[0][4])

                self._logger.info('Connected!')

                server_hello = self.socket.recv(1024)
                self._logger.info(server_hello.strip(" \r\n"))

                # Try to get my version
                try:
                    version = pkg_resources.get_distribution(
                        'pymma').version
                except:
                    version = 'GIT'

                # Login
                self._logger.info("login %s (PYMMA %s)" % (
                    self.callsign, version))
                self.socket.send(
                    "user %s pass %s vers PYMMA %s filter "
                    "r/38/-171/1\r\n" % (
                        self.callsign, self.passcode, version))

                server_return = self.socket.recv(1024)
                self._logger.info(server_return.strip(" \r\n"))

                self.connected = True
            except socket.error as ex:
                self._logger.warn(
                    "Error when connecting to %s:%d: '%s'" %
                    (self.server, self.port, str(ex)))
                time.sleep(1)

    def _disconnect(self):
        try:
            self.socket.close()
        except:
            pass

    def send(self, frame):
        try:
            # wait 10sec for queue slot, then drop the data
            self._sending_queue.put(frame, True, 10)
        except Queue.Full:
            self._logger.warn(
                "Lost TX data (queue full): '%s'" % frame.export(False))

    def _socket_worker(self):
        """
        Running as a thread, reading from socket, sending queue to socket
        """
        while self._running:
            try:
                try:
                    # wait max 1sec for new data
                    frame = self._sending_queue.get(True, 1)
                    self._logger.debug("sending: %s" % frame.export(False))
                    raw_frame = "%s\r\n" % frame.export()
                    totalsent = 0
                    while totalsent < len(raw_frame):
                        sent = self.socket.send(raw_frame[totalsent:])
                        if sent == 0:
                            raise socket.error(
                                0,
                                "Failed to send data - "
                                "number of sent bytes: 0")
                        totalsent += sent
                except Queue.Empty:
                    pass

                # (try to) read from socket to prevent buffer fillup
                self.socket.setblocking(0)
                try:
                    self.socket.recv(40960)
                except socket.error as e:
                    if not e.errno == 11:
                        # if the error is other than 'rx queue empty'
                        raise
                self.socket.setblocking(1)
            except socket.error as ex:
                # possible errors on IO:
                # [Errno  11] Buffer is empty (maybe not when using blocking
                #             sockets)
                # [Errno  32] Broken Pipe
                # [Errno 104] Connection reset by peer
                # [Errno 110] Connection time out

                rand_sleep = random.randint(1, 20)

                if ex.errno == errno.EAGAIN or ex.errno == errno.EWOULDBLOCK:
                    self._logger.warn(
                        'Connection issue, sleeping for %ss: "%s"',
                        rand_sleep, str(e))
                    time.sleep(rand_sleep)
                else:
                    self._logger.warn(
                        'Connection issue, sleeping for %ss: "%s"',
                        rand_sleep, str(e))
                    time.sleep(rand_sleep)

                    # try to reconnect
                    self._connect()

        self._logger.debug('Sending thread exit.')


class Multimon(object):

    """PYMMA Multimon Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.constants.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.constants.LOG_LEVEL)
        _console_handler.setFormatter(pymma.constants.LOG_FORMAT)
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

                sample_rate = str(pymma.constants.SAMPLE_RATE)

                # Allow use of 'rx_fm' for Soapy/hackrf
                rtl_cmd = self.config['rtl'].get('command', 'rtl_fm')

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
                    rtl_args.extend(['-d', str(device_index)])

                _rtl_cmd = []
                _rtl_cmd.extend([rtl_cmd])
                _rtl_cmd.extend(rtl_args)
                _rtl_cmd.extend(['-'])

                self._logger.debug('_rtl_cmd=%s', _rtl_cmd)

                proc_src = subprocess.Popen(
                    _rtl_cmd,
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
            read_line = self.subprocs['mm'].stdout.readline().strip()
            matched_line = START_FRAME_REX.match(read_line)
            if matched_line:
                self.frame_handler(matched_line.group(1))
