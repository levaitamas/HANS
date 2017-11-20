#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MIDI OSC TESTER

Copyright (C) 2017-     Tamás Lévai    <levait@tmit.bme.hu>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import time
import pyo

class MidiHandler:
    def __init__(self, ip, port, addr):
        self.rawm = pyo.RawMidi(handle_midievent)
        self.osc_sender = pyo.OscDataSend('m', port, addr, host=ip)

def handle_midievent(status, note, velocity):
    print("%s %s %s" % (status, note, velocity))
    midihandler.osc_sender.send([[0, status, note, velocity]])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MidiOSCTester')
    parser.add_argument('-i', '--ip',
                        help='IP address to listen',
                        type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port',
                        help='UDP port to listen',
                        type=int, default=5005)
    parser.add_argument('-a', '--address',
                        help='OSC address',
                        type=str, default='/hans/midi')
    parser.add_argument('-m', '--midi',
                        help='Input MIDI channel number',
                        type=int, default=None)
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose mode',
                        action='store_true')
    args = parser.parse_args()

    if int(''.join(map(str, pyo.getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")

    server = pyo.Server(duplex=0, audio='jack', jackname='MidiOSCTester')

    if args.verbose:
        server.setVerbosity(8)

    if args.midi:
        server.setMidiInputDevice(args.midi)
    else:
        pyo.pm_list_devices()
        inid = -1
        while (inid > pyo.pm_count_devices()-1 and inid != 99) or inid < 0:
            inid = int(input("Please select input ID [99 for all]: "))
            server.setMidiInputDevice(inid)

    server.boot()
    server.start()

    midihandler = MidiHandler(args.ip, args.port, args.address)

    while True:
        time.sleep(2)
