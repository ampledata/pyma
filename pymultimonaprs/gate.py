#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pymultimonaprs Package."""

import errno
import itertools
import logging
import logging.handlers
import pkg_resources
import Queue
import random
import socket
import threading
import time

import pymultimonaprs.constants

__author__ = 'Dominik Heidler <dominik@heidler.eu>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


class IGate(object):

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(pymultimonaprs.constants.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(pymultimonaprs.constants.LOG_LEVEL)
        _console_handler.setFormatter(pymultimonaprs.constants.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, callsign, passcode, gateways, preferred_protocol):
        self.gateways = itertools.cycle(gateways)
        self.callsign = callsign
        self.passcode = passcode
        self.preferred_protocol = preferred_protocol
        self.socket = None
        self._sending_queue = Queue.Queue(maxsize=1)
        self._connect()
        self._running = True
        self._worker = threading.Thread(target=self._socket_worker)
        self._worker.setDaemon(True)
        self._worker.start()
        self.server = ''
        self.port = 0

    def exit(self):
        self._running = False
        self._disconnect()

    def _connect(self):
        connected = False
        while not connected:
            try:
                # Connect
                gateway = next(self.gateways)
                self.server, self.port = gateway.split(':')
                self.port = int(self.port)

                if self.preferred_protocol == 'ipv6'
                    addrinfo = socket.getaddrinfo(
                        self.server, self.port, socket.AF_INET6)
                elif self.preferred_protocol == 'ipv4':
                    addrinfo = socket.getaddrinfo(
                        self.server, self.port, socket.AF_INET)
                else:
                    addrinfo = socket.getaddrinfo(self.server, self.port)

                self.socket = socket.socket(*addrinfo[0][0:3])
                self._logger.info(
                    "connecting... %s:%i" % (addrinfo[0][4], self.port))
                self.socket.connect(addrinfo[0][4])

                self._logger.info('Connected!')

                server_hello = self.socket.recv(1024)
                self._logger.info(server_hello.strip(" \r\n"))

                # Try to get my version
                try:
                    version = pkg_resources.get_distribution(
                        'pymultimonaprs').version
                except:
                    version = 'GIT'

                # Login
                self._logger.info("login %s (PyMultimonAPRS %s)" % (
                    self.callsign, version))
                self.socket.send(
                    "user %s pass %s vers PyMultimonAPRS %s filter "
                    "r/38/-171/1\r\n" % (
                        self.callsign, self.passcode, version))

                server_return = self.socket.recv(1024)
                self._logger.info(server_return.strip(" \r\n"))

                connected = True
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
