pymma - Python Multimon APRS
****************************

pymma is an RF to APRS-IS gateway supporting several backends:

- Pulseaudio
- ALSA
- RTL-SDR
- HackRF (via Soapy)

You can inject frames directly from RF (SDR), or from an audio source (ALSA).

pymma vs. pymultimonaprs
========================

pymma is derived from Dominik Heidler's work on https://github.com/asdil12/pymultimonaprs

Credit for the majority of the work on pymma goes to @asdil12, et al. pymma is
intended as a fork from pymultimonaprs. While I plan to match capabilities and
contribute back to the pymultimonaprs project, pymma will vary in several aspects.

Every intention has been made to credit Dominik throughout this code, and to
maintain and uphold GPL (to the best of my understanding).

It goes without saying that @asdil12 did most of the heavy lifting :).

Versions
========

- 1.3.x will be the last branch to support Python 2.7.x.
- 2.x will support Python 3.6.x only.

Installation
============

- Install multimon-ng
- Install rtl-sdr or soapy (for RTL-SDR backend)
- Run `make install`

Configuration
=============

Edit `/etc/pymma.json`

Backend
^^^^^^^

Set the source to `rtl`, `alsa`, or `pulse` to select the backend

Status
^^^^^^

Set the status `text`, or set a status `file` - the content of this file will be read at runtime and sent as status.
This way you can eg. monitor your battery status using APRS-IG.
Set both `text` and `file` to `false` to disable status beacon.

Position Ambiguity
^^^^^^^^^^^^^^^^^^

To hide your exact position you can set the ambiguity value to a value from 0 to 4.
- 0 will not hide anything
- 1 will decrease precision to 1/10 of a min
- 2 will decrease precision to 1 min
- 3 will decrease precision to 10 min
- 4 will decrease precision to 1°

Weather
^^^^^^^

You can set `weather` to a json-file. eg: `"weather": "/path/to/weather.json",`
If you don't want do send weather date, just leave it on `false`.
This will be read in like the status-file and can look like that::

    {
    	"timestamp": 1366148418,
    	"wind": {
    		"speed": 10,
    		"direction": 240,
    		"gust": 200
    	},
    	"temperature": 18.5,
    	"rain": {
    		"rainlast1h": 10,
    		"rainlast24h": 20,
    		"rainmidnight": 15
    	},
    	"humidity": 20,
    	"pressure": 1013.25
    }


Legend
^^^^^^

- `timestamp` is seconds since epoch - **must** be included
- `wind`
	- `speed` is in km/h
	- `direction` is in deg
	- `gust` is in km/h
- `temperature` is in °C
- `rain`
	- `rainlast1h` is in mm
	- `rainlast24h` is in mm
	- `rainmidnight` is in mm
- `humidity` is in %
- `pressure` is in hPa

The timestamp **must** be included - everything else is optional.

Symbol
^^^^^^

The correct symbol is already selected.
If you still want to change it, you can find the symbol table [here](https://github.com/asdil12/pymma/wiki/Symbol-Table).

IPv4 / IPv6
^^^^^^^^^^^

To select a protocol you can set `preferred_protocol` to `ipv4`, `ipv6` or `any`.
You use a raw IPv6 address as a gateway like this: `"[2000::1234]:14580"`.

Running
=======

- It is recommended you run pymma with supervisor or systemd.

- Run `systemctl start pymma` or just `pymma -v` for testing.


Chef Cookbook
^^^^^^^^^^^^^

See https://github.com/ampledata/cookbook-pymma

Source
======
Github: https://github.com/ampledata/pymma

Author
======
Greg Albrecht W2GMD <oss@undef.net>

Copyright
=========
Copyright 2016 Dominik Heidler

License
=======
GNU General Public License, Version 3
