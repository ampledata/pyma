#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2016 Dominik Heidler'
__license__ = 'GNU General Public License, Version 3'

import sys

def generate(callsign):
    # This method derived from the xastir project under a GPL license.
    seed = 0x73E2

    odd = True
    key = seed
    for char in callsign.upper():
        proc_char = ord(char)
        if odd:
            proc_char <<= 8
        key = key ^ proc_char
        odd = not odd
    key &= 0x7FFF
    return key

if __name__ == '__main__':
    if len(sys.argv) > 1:
        callsign = sys.argv[1]
        code = generate(callsign)
        print "Key for %s: %i" % (callsign.upper(), code)
    else:
        print "Tool to generate key for APRS-IS network"
        print "usage: %s CALLSIGN"
