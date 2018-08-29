#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Classes."""

import errno
import itertools
import logging
import queue
import random
import socket
import subprocess
import threading
import time

import pkg_resources
import pynmea2
import requests
import serial

<<<<<<< HEAD
=======
import aprslib  # type: ignore
from aprslib.packets.base import APRSPacket  # type: ignore

>>>>>>> feature/python3_support
import pymma

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


class IGateThread(threading.Thread):  # pylint: disable=too-many-instance-attributes

    """PYMMA IGate Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.LOG_LEVEL)
        _console_handler.setFormatter(pymma.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, frame_queue: queue.Queue, config: dict) -> None:
        super(IGateThread, self).__init__()
        self.frame_queue = frame_queue
        self.config = config

        self.server: str = ''
        self.port: int = 0
        self.connected: bool = False
        self.socket: socket.socket = socket.socket

        self.callsign: str = self.config['callsign']
        self.passcode: str = self.config['passcode']
        self.gateways: list = itertools.cycle(self.config['gateways'])
        self.proto: str = self.config.get('proto', 'any')

        self.daemon = True
        self._stopper = threading.Event()

        # Try to get my version
        try:
            self.version = pkg_resources.get_distribution(
                'pymma').version
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception(exc)
            self.version = 'GIT'

    def stop(self):
        """
        Stop the thread at the next opportunity.
        """
        self._disconnect()
        self._stopper.set()

    def stopped(self):
        """
        Checks if the thread is stopped.
        """
        return self._stopper.isSet()

    def run(self):
        """
        Runs the thread.
        """
        self._logger.info('Starting IGate Thread="%s"', self)
        self._tcp_worker()

    def _connect(self) -> None:
        """
        Connects to the APRS-IS network.
        """
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
                self._logger.info('server_hello="%s"', server_hello)

                # Login
                login_info = bytes(
                    ('user {} pass {} vers PYMMA {} filter m/10\r\n'.format(
                        self.callsign, self.passcode, self.version)),
                    'utf8'
                )
                self.socket.send(login_info)

                server_return = self.socket.recv(1024)
                self._logger.info('server_return="%s"', server_return)

                self.connected = True
            except socket.error as ex:
                self._logger.warning(
                    "Error when connecting to %s:%d: '%s'",
                    self.server, self.port, str(ex))
                time.sleep(1)

    def _disconnect(self) -> None:
        """
        Disconnects/closes socket.
        """
        try:
            self.socket.close()
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.warning('Raised Exception trying to close socket:')
            self._logger.exception(exc)

    def send(self, frame: APRSPacket) -> None:
        """
        Adds frame to APRS-IS queue.
        """
        try:
            # wait 10sec for queue slot, then drop the data
            self.frame_queue.put(frame, True, 10)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception(exc)
            self._logger.warning(
                'Lost TX data (queue full): "%s"', frame)

    def _http_worker(self) -> None:
        self._logger.info('Running HTTP Worker Thread.')

        with requests.Session() as session:
            session.headers.update(
                {'content-type': 'application/octet-stream'})

            while not self.stopped():
                try:
                    # wait max 1sec for new data
                    frame = self.frame_queue.get(True, 1)
                    if not frame:
                        next

                    self._logger.info('Sending via HTTP frame="%s"', frame)

                    # Login
                    login_info = (
                        'user {} pass {} vers PYMMA {}').format(
                            self.callsign, self.passcode, self.version)
                    data = '\n'.join([login_info, str(frame)])

                    response = session.post(
                        'http://noam.aprs2.net:8080', data=data)
                    self._logger.debug(
                        'response="%s" response.text="%s"',
                        response, response.text)
                    #session.raise_for_error()

                except queue.Empty:
                    pass

        self._logger.debug('Sending thread exit.')

    def _udp_worker(self) -> None:
        self._logger.info('Running UDP Worker Thread.')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while not self.stopped():
            try:
                # wait max 1sec for new data
                frame = self.frame_queue.get(True, 1)
                if not frame:
                    next

                self._logger.info('Sending via UDP frame="%s"', frame)
                login = 'user {} pass {} vers PYMMA {}'.format(
                    self.callsign, self.passcode, self.version)
                raw_frame = bytes('\n'.join([login, str(frame)]), 'utf8')
                self.socket.sendto(raw_frame, ('noam.aprs2.net', 8080))
            except queue.Empty:
                pass
        self._logger.debug('UDP Worker Thread Exit.')

    def _tcp_worker(self) -> None:
        """
        Running as a thread, reading from socket, sending queue to socket
        """
        self._logger.info('Running TCP Worker Thread %s', self)

        self._connect()

        while not self.stopped():
            try:
                try:
                    # wait max 1sec for new data
                    frame = self.frame_queue.get(True, 1)
<<<<<<< HEAD
                    self._logger.info('Sending: "%s"', frame)
                    raw_frame = "%s\r\n" % frame
=======
                    if not frame:
                        next
                    self._logger.info('Sending via TCP frame="%s"', frame)
                    raw_frame = bytes(str(frame) + '\n', 'utf8')

>>>>>>> feature/python3_support
                    total_sent = 0
                    while total_sent < len(raw_frame):
                        sent = self.socket.send(raw_frame[total_sent:])
                        if sent == 0:
                            raise socket.error(
<<<<<<< HEAD
                                0, "Failed to send data, 0 bytes sent.")
                        total_sent += sent
                except Queue.Empty as ex:
                    #
                    # Normally you should log all catched exceptions, only
                    # Queue uses the anti-pattern of try/catch for flow
                    # control, so we're not going to log it in this case.
                    #
                    # See: http://wiki.c2.com/?DontUseExceptionsForFlowControl
                    #
                    # self._logger.exception(ex)
=======
                                0,
                                'Failed to send data - '
                                'number of sent bytes: 0')
                        total_sent += sent
                        self._logger.debug(
                            'total_sent="%s" sent="%s"', total_sent, sent)
                except queue.Empty:
>>>>>>> feature/python3_support
                    pass

                # (try to) read from socket to prevent buffer fillup
                self.socket.setblocking(False)

                try:
<<<<<<< HEAD
                    self.socket.recv(40960)
                except socket.error as ex:
                    # "[Errno 11] Resource temporarily unavailable" is OK.
                    # self._logger.exception(ex)
                    if not ex.errno == 11:
                        self._logger.exception(ex)
                        # if the error is other than 'rx queue empty'
                        raise
                self.socket.setblocking(1)
            except socket.error as ex:
                # Possible errors on IO:
                #
=======
                    self.socket.recv(4096)
                except socket.error as exc:
                    if exc.errno != 11:
                        # if the error is other than 'rx queue empty'
                        raise

                self.socket.setblocking(True)
            except socket.error as exc:
                # possible errors on IO:
>>>>>>> feature/python3_support
                # [Errno  11] Buffer is empty (maybe not when using blocking
                #             sockets)
                # [Errno  32] Broken Pipe
                # [Errno 104] Connection reset by peer
                # [Errno 110] Connection time out
<<<<<<< HEAD
                #
                self._logger.exception(ex)
=======
                self._logger.exception(exc)
>>>>>>> feature/python3_support

                rand_sleep = random.randint(1, 20)

                if exc.errno == errno.EAGAIN or exc.errno == errno.EWOULDBLOCK:
                    self._logger.warning(
                        'Connection issue, sleeping for %ss: "%s"',
                        rand_sleep, str(exc))
                    time.sleep(rand_sleep)
                else:
                    self._logger.warning(
                        'Connection issue, sleeping for %ss: "%s"',
                        rand_sleep, str(exc))
                    time.sleep(rand_sleep)

                    # try to reconnect
                    self._connect()

        self._logger.info('Sending thread exit.')


class BeaconThread(threading.Thread):

    """
    Threaded Beacon.
    """

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.LOG_LEVEL)
        _console_handler.setFormatter(pymma.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, igate, config):
        super(BeaconThread, self).__init__()
        self.igate = igate
        self.config = config
        self.daemon = True
        self._stopper = threading.Event()

    def stop(self):
        """
        Stop the thread at the next opportunity.
        """
        self._stopper.set()

    def stopped(self):
        """
        Checks if the thread is stopped.
        """
        return self._stopper.isSet()

    def run(self):
        """
        Runs the thread.
        """
        self._logger.info('Starting Beacon Thread="%s"', self)

        beacon_config = self.config.get('beacon')

        bcargs = {
            'lat': float(beacon_config['location']['lat']),
            'lng': float(beacon_config['location']['lng']),
            'callsign': self.igate.callsign,
            'table': beacon_config['table'],
            'symbol': beacon_config['symbol'],
            'comment': beacon_config['comment'],
            'ambiguity': beacon_config.get('ambiguity', 0),
        }

        bcargs_status = {
            'callsign': self.igate.callsign,
            'status': beacon_config['status'],
        }

        bcargs_weather = {
            'callsign': self.igate.callsign,
            'weather': beacon_config['weather'],
        }

        while not self.stopped():
            # Position
            frame = pymma.get_beacon_frame(**bcargs)
            if frame:
                self.igate.send(frame)

            # Status
            frame = pymma.get_status_frame(**bcargs_status)
            if frame:
                self.igate.send(frame)

            # Weather
            frame = pymma.get_weather_frame(**bcargs_weather)
            if frame:
                self.igate.send(frame)

            time.sleep(beacon_config['send_every'])


class GPSBeaconThread(threading.Thread):

    """
    Threaded Beacon.
    """

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.LOG_LEVEL)
        _console_handler.setFormatter(pymma.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, igate, config, gps):
        super(BeaconThread, self).__init__()
        self.igate = igate
        self.config = config
        self.gps = gps
        self.daemon = True
        self._stopper = threading.Event()

    def stop(self):
        """
        Stop the thread at the next opportunity.
        """
        self._stopper.set()

    def stopped(self):
        """
        Checks if the thread is stopped.
        """
        return self._stopper.isSet()

    def run(self):
        """
        Runs the thread.
        """
        self._logger.info('Starting Beacon Thread="%s"', self)

        beacon_config = self.config.get('beacon')


        bcargs_status = {
            'callsign': self.igate.callsign,
            'status': beacon_config['status'],
        }

        bcargs_weather = {
            'callsign': self.igate.callsign,
            'weather': beacon_config['weather'],
        }

        while not self.stopped():
            # Position
            bcargs = {
                'lat': float(self.gps.gps_props['latitude']),
                'lng': float(self.gps.gps_props['longitude']),
                'altitude': self.gps.gps_props.get('altitude', 0),
                'callsign': self.igate.callsign,
                'table': beacon_config['table'],
                'symbol': beacon_config['symbol'],
                'comment': beacon_config['comment'],
                'ambiguity': beacon_config['location'].get('ambiguity', 0),
            }

            frame = pymma.get_beacon_frame(**bcargs)
            if frame:
                self.igate.send(frame)

            # Status
            frame = pymma.get_status_frame(**bcargs_status)
            if frame:
                self.igate.send(frame)

            # Weather
            frame = pymma.get_weather_frame(**bcargs_weather)
            if frame:
                self.igate.send(frame)

            time.sleep(beacon_config['send_every'])


class MultimonThread(threading.Thread):

    """PYMMA SourceThread Class."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.LOG_LEVEL)
        _console_handler.setFormatter(pymma.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, frame_queue: queue.Queue, config: dict) -> None:
        super(MultimonThread, self).__init__()
        self.frame_queue = frame_queue
        self.config = config
        self.processes: dict = {}
        self.daemon = True
        self._stopper = threading.Event()

    def _workers(self) -> None:
        self._logger.info('Starting from source="%s"', self.config['source'])

        if self.config['source'] == 'pulse':
            multimon_cmd = ['multimon-ng', '-a', 'AFSK1200', '-A']

            multimon_proc = subprocess.Popen(
                multimon_cmd,
                stdout=subprocess.PIPE,
                stderr=open('/dev/null')
            )
        else:
            sample_rate = str(pymma.SAMPLE_RATE)

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

    def run(self) -> None:
        self._workers()
        while not self.stopped():
            read_line = self.processes['multimon'].stdout.readline().strip()
            matched_line = pymma.START_FRAME_REX.match(read_line)

            if matched_line:
                frame = matched_line.group(1)
                if not frame:
                    next
                self._logger.debug('Matched frame="%s"', frame)
                self.handle_frame(frame)

    def stop(self):
        """
        Stop the thread at the next opportunity.
        """
        for name in ['multimon', 'src']:
            try:
                proc = self.processes[name]
                proc.terminate()
            except Exception as exc:  # pylint: disable=broad-except
                self._logger.exception(
                    'Raised Exception while trying to terminate %s: %s',
                    name, exc)
        self._stopper.set()

<<<<<<< HEAD
    def _multimon_worker(self):
        while self._running:
            read_line = self.processes['multimon'].stdout.readline().strip()
            matched_line = pymma.START_FRAME_REX.match(read_line)
            if matched_line:
                self.handle_frame(matched_line.group(1))
=======
    def stopped(self):
        """
        Checks if the thread is stopped.
        """
        return self._stopper.isSet()
>>>>>>> feature/python3_support

    def reject_frame(self, frame: APRSPacket) -> bool:
        """Determines if the frame should be rejected."""
        if set(self.config.get(
                'reject_paths',
                pymma.REJECT_PATHS)).intersection(frame.path):
<<<<<<< HEAD
            self._logger.warn(
=======
            self._logger.warning(
>>>>>>> feature/python3_support
                'Rejected frame with REJECTED_PATH: "%s"', frame)
            return True
        elif (bool(self.config.get('reject_internet')) and
              frame.text.startswith('}')):
            self._logger.warning(
                'Rejected frame from the Internet: "%s"', frame)
            return True

        return False

<<<<<<< HEAD
    def handle_frame(self, frame):
        try:
            aprs_frame = aprs.Frame(frame)
            self._logger.debug('aprs_frame=%s', aprs_frame)

            if bool(self.config.get('append_callsign')):
                aprs_frame.path.extend(['qAR', self.config['callsign']])

            if not self.reject_frame(aprs_frame):
                self.frame_queue.put(aprs_frame, True, 10)
        except aprs.BadCallsignError as ex:
            self._logger.exception(ex)
            pass
=======
    def handle_frame(self, frame: bytes) -> None:
        """Handles the Frame from the APRS Decoder."""
        self._logger.debug('Handling frame="%s"', frame)

        aprs_packet = None
        decoded_frame = None

        try:
            decoded_frame = frame.decode()
        except Exception as exc:
            self._logger.warning(
                'Failed to decode() frame="%s"', frame)
            self._logger.exception(exc)

        self._logger.debug('decoded_frame="%s"', decoded_frame)

        if not decoded_frame:
            return

        try:
            aprs_packet = APRSPacket(decoded_frame)
        except Exception as exc:
            self._logger.warning(
                'Failed to APRSPacket() frame="%s"', decoded_frame)
            self._logger.exception(exc)

        self._logger.debug('aprs_packet="%s"', aprs_packet)

        if not aprs_packet:
            return

        if bool(self.config.get('append_callsign')):
            aprs_packet.path.extend(['qAR', self.config['callsign']])

        if not self.reject_frame(aprs_packet):
            try:
                self.frame_queue.put(aprs_packet, True, 10)
            except queue.Full as exc:
                self._logger.exception(exc)
                self._logger.warning(
                    'Lost TX data (queue full): "%s"', frame)


class SerialGPSPoller(threading.Thread):

    """Threadable Object for polling a serial NMEA-compatible GPS."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymma.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymma.LOG_LEVEL)
        _console_handler.setFormatter(pymma.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, serial_port, serial_speed):
        super(SerialGPSPoller, self).__init__()
        self._serial_port = serial_port
        self._serial_speed = serial_speed

        self.gps_props = {}
        for prop in pymma.NMEA_PROPERTIES:
            self.gps_props[prop] = None

        self._serial_int = serial.Serial(
            self._serial_port, self._serial_speed, timeout=1)

        self.daemon = True
        self._stopper = threading.Event()

    def stop(self):
        """
        Stop the thread at the next opportunity.
        """
        self._stopper.set()

    def stopped(self):
        """
        Checks if the thread is stopped.
        """
        return self._stopper.isSet()

    def run(self):
        streamreader = pynmea2.NMEAStreamReader(self._serial_int)
        time.sleep(pymma.GPS_WARM_UP)
        while not self.stopped():
            for msg in streamreader.next():
                for prop in pymma.NMEA_PROPERTIES:
                    if getattr(msg, prop, None) is not None:
                        self.gps_props[prop] = getattr(msg, prop)
>>>>>>> feature/python3_support
