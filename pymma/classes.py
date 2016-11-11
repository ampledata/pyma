#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Classes."""

import errno
import itertools
import logging
import logging.handlers
import Queue
import random
import socket
import subprocess
import threading
import time

import aprs
import pkg_resources

import pymma.constants

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


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

    def __init__(self, frame_queue, callsign, passcode, gateways, proto):
        self.frame_queue = frame_queue
        self.callsign = callsign
        self.passcode = passcode
        self.gateways = itertools.cycle(gateways)
        self.proto = proto

        self.socket = None
        self.server = ''
        self.port = 0
        self.connected = False

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

                if self.proto == 'ipv6':
                    addrinfo = socket.getaddrinfo(
                        self.server, self.port, socket.AF_INET6)
                elif self.proto == 'ipv4':
                    addrinfo = socket.getaddrinfo(
                        self.server, self.port, socket.AF_INET)
                else:
                    addrinfo = socket.getaddrinfo(self.server, self.port)

                self.socket = socket.socket(*addrinfo[0][0:3])

                self._logger.info(
                    "Connecting to %s:%i", addrinfo[0][4][0], self.port)

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
                self.socket.send(
                    "user %s pass %s vers PYMMA %s filter "
                    "r/38/-171/1\r\n" % (
                        self.callsign, self.passcode, version))

                server_return = self.socket.recv(1024)
                self._logger.info(server_return.strip(" \r\n"))

                self.connected = True
            except socket.error as ex:
                self._logger.warn(
                    "Error when connecting to %s:%d: '%s'",
                    self.server, self.port, str(ex))
                time.sleep(1)

    def _disconnect(self):
        try:
            self.socket.close()
        except:
            pass

    def send(self, frame):
        try:
            # wait 10sec for queue slot, then drop the data
            self.frame_queue.put(frame, True, 10)
        except Queue.Full:
            self._logger.warn(
                "Lost TX data (queue full): '%s'", frame)

    def _socket_worker(self):
        """
        Running as a thread, reading from socket, sending queue to socket
        """
        while self._running:
            try:
                try:
                    # wait max 1sec for new data
                    frame = self.frame_queue.get(True, 1)
                    self._logger.debug("Sending: %s", frame)
                    raw_frame = "%s\r\n" % frame
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
                        rand_sleep, str(ex))
                    time.sleep(rand_sleep)
                else:
                    self._logger.warn(
                        'Connection issue, sleeping for %ss: "%s"',
                        rand_sleep, str(ex))
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

    def __init__(self, frame_queue, config):
        self.frame_queue = frame_queue
        self.config = config

        self.processes = {}

        self._start()
        self._running = True
        self._worker = threading.Thread(target=self._multimon_worker)
        self._worker.setDaemon(True)
        self._worker.start()

    def exit(self):
        self._running = False
        self._stop()

    def _start(self):
        self._logger.debug('source=%s', self.config['source'])

        if self.config['source'] == 'pulse':
            multimon_cmd = ['multimon-ng', '-a', 'AFSK1200', '-A']

            multimon_proc = subprocess.Popen(
                multimon_cmd,
                stdout=subprocess.PIPE,
                stderr=open('/dev/null')
            )
        else:
            sample_rate = str(pymma.constants.SAMPLE_RATE)

            if self.config['source'] == 'rtl':
                # Allow use of 'rx_fm' for Soapy/HackRF
                rtl_cmd = self.config['rtl'].get('command', 'rtl_fm')

                frequency = str(int(self.config['rtl']['freq'] * 1e6))
                ppm = str(self.config['rtl']['ppm'])
                gain = str(self.config['rtl']['gain'])

                device_index = str(self.config['rtl'].get('device_index', '0'))

                if self.config['rtl'].get('offset_tuning') is not None:
                    enable_option = 'offset'
                else:
                    enable_option = 'none'

                src_cmd = [
                    rtl_cmd,
                    '-f', frequency,
                    '-s', sample_rate,
                    '-p', ppm,
                    '-g', gain,
                    '-E', enable_option,
                    '-d', device_index,
                    '-'
                ]
            elif self.config['source'] == 'alsa':
                alsa_device = self.config['alsa']['device']

                src_cmd = [
                    'arecord',
                    '-D', alsa_device,
                    '-r', sample_rate,
                    '-f', 'S16_LE',
                    '-t', 'raw',
                    '-c', '1',
                    '-'
                ]

            self._logger.debug('src_cmd="%s"', ' '.join(src_cmd))

            src_proc = subprocess.Popen(
                src_cmd,
                stdout=subprocess.PIPE
            )

            self.processes['src'] = src_proc

            multimon_cmd = [
                'multimon-ng', '-a', 'AFSK1200', '-A', '-t', 'raw', '-']
            self._logger.debug('multimon_cmd="%s"', ' '.join(multimon_cmd))

            multimon_proc = subprocess.Popen(
                multimon_cmd,
                stdin=self.processes['src'].stdout,
                stdout=subprocess.PIPE
            )

        self.processes['multimon'] = multimon_proc

    def _stop(self):
        for name in ['multimon', 'src']:
            try:
                proc = self.processes[name]
                proc.terminate()
            except Exception as ex:
                self._logger.exception(
                    'Raised Exception while trying to terminate %s: %s',
                    name, ex)

    def _multimon_worker(self):
        while self._running:
            read_line = self.processes['multimon'].stdout.readline().strip()
            matched_line = pymma.constants.START_FRAME_REX.match(read_line)
            if matched_line:
                self.handle_frame(matched_line.group(1))

    def reject_frame(self, frame):
        if set(self.config.get(
                'reject_paths',
                pymma.constants.REJECT_PATHS)).intersection(frame.path):
            self._logger.warn(
                'Rejected frame with REJECTED_PATH: "%s"', frame)
            return True
        elif (bool(self.config.get('reject_internet')) and
              frame.text.startswith('}')):
            self._logger.warn(
                'Rejected frame from the Internet: "%s"', frame)
            return True

        return False

    def handle_frame(self, frame):
        frame = aprs.APRSFrame(frame)
        self._logger.debug('frame=%s', frame)

        if bool(self.config.get('append_callsign')):
            frame.path.extend(['qAR', self.config['callsign']])

        if not self.reject_frame(frame):
            self.frame_queue.put(frame, True, 10)
