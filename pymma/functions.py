#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PYMMA Beacon functions."""

import datetime
import json
import os

import aprslib

from aprslib.packets.base import APRSPacket

import pymma

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'


def process_ambiguity(position: str, ambiguity: int) -> str:
    """
    Recalculate Postition with given Ambiguity.
    """
    position_ba = bytearray(position, 'utf8')
    for i in range(0, ambiguity):
        print(locals())
        if i > 1:
            # skip the dot
            i += 1
        # skip the direction
        i += 2
        position_ba[-i] = ord(' ')
    return position_ba.decode()


def encode_lat(lat: float) -> str:
    """
    Encode Latitude in DDMMSS format.
    """
    lat_dir = 'N' if lat > 0 else 'S'
    lat_abs = abs(lat)
    lat_deg = int(lat_abs)
    lat_min = (lat_abs % 1) * 60
    #return "%02i%05.2f%c" % (lat_deg, lat_min, lat_dir)
    return "%02i%05.2f" % (lat_deg, lat_min)


def encode_lng(lng: float):
    """
    Encode Longitude in DDMMSS format.
    """
    lng_dir = 'E' if lng > 0 else 'W'
    lng_abs = abs(lng)
    lng_deg = int(lng_abs)
    lng_min = (lng_abs % 1) * 60
    #return "%03i%05.2f%c" % (lng_deg, lng_min, lng_dir)
    return "%03i%05.2f" % (lng_deg, lng_min)


def get_beacon_frame(lat: float, lng: float, callsign: str, table: str,  # NOQA pylint: disable=too-many-arguments
                     symbol: str, comment: str,
                     ambiguity: float) -> APRSPacket:
    """
    Generate beacon frame.
    """
    enc_lat = process_ambiguity(encode_lat(lat), ambiguity)
    enc_lng = process_ambiguity(encode_lng(lng), ambiguity)

    frame = aprslib.packets.PositionReport()
    frame.fromcall = callsign
    frame.tocall = 'APYSPM'
    frame.latitude = lat
    frame.longitude = lng
    frame.symbol = symbol
    frame.table = table
    frame.comment = comment
    return frame


def get_status_frame(callsign: str, status: str) -> APRSPacket:
    """
    Generate status frame.
    """
    status_text = None
    if status['file'] and os.path.exists(status['file']):
        status_text = open(status['file']).read().decode('UTF-8').strip()
    elif status['text']:
        status_text = status['text']

    if not status_text:
        return None

    frame = APRSPacket()
    frame.fromcall = callsign
    frame.tocall = 'APYSPM'
    frame.path = ['TCPIP*']
    frame.body = '>' + status_text
    return frame


def get_weather_frame(callsign, weather):  # NOQA pylint: disable=too-many-branches,too-many-statements
    """
    Generate weather frame.
    """
    try:
        w = json.load(open(weather))

        # Convert to imperial and encode

        # Timestamp
        wenc = datetime.datetime.utcfromtimestamp(
            int(w['timestamp'])).strftime('%m%d%H%M')

        # Wind
        wind = w.get('wind', {})
        if 'direction' in wind:
            wenc += "c%03d" % wind['direction']
        else:
            wenc += "c..."
        if 'speed' in wind:
            si = round(wind['speed'] * 0.621371192)
            wenc += "s%03d" % si
        else:
            wenc += "s..."
        if 'gust' in wind:
            si = round(wind['gust'] * 0.621371192)
            wenc += "g%03d" % si
        else:
            wenc += "g..."

        # Temperature
        if 'temperature' in w:
            wenc += "t%03d" % round(w['temperature'] / (float(5)/9) + 32)
        else:
            wenc += "t..."

        # Rain
        rain = w.get('rain', {})
        if 'rainlast1h' in rain:
            si = round(rain['rainlast1h'] / 25.4)
            wenc += "r%03d" % si
        else:
            wenc += "r..."

        if 'rainlast24h' in rain:
            si = round(rain['rainlast24h'] / 25.4)
            wenc += "p%03d" % si
        else:
            wenc += "p..."

        if 'rainmidnight' in rain:
            si = round(rain['rainmidnight'] / 25.4)
            wenc += "P%03d" % si
        else:
            wenc += "P..."

        # Humidity
        if 'humidity' in w:
            h = w['humidity']
            if h == 0:
                h = 1
            if h == 100:
                h = 0
            wenc += "h%02d" % h
        else:
            wenc += "h.."

        # Atmospheric pressure
        if 'pressure' in w:
            wenc += "b%04d" % round(w['pressure'] * 10)

        payload = "_%sPyMM" % wenc
        #return make_frame(callsign, payload)
    except:
        return
