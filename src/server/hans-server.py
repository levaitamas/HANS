#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HANS SERVER

Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>

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
import json
import pyo
import random
import signal
import sys
import threading
import time

import lib.choosers
import lib.modulators
import lib.seedgens
import lib.sigprocs
import lib.util
from lib.module_base import HansModule
from lib.sample_handling import SampleBank


class HansMain(object, metaclass=lib.util.Singleton):
    def __init__(self, args):
        self.init_modules_from_config(args.configfile)

    def init_modules_from_config(self, configfile):
        with open(configfile) as config_file:
            config = json.load(config_file)
            modules = config['modules']
            self.modules = {
                'samplebank': SampleBank(sample_root=args.sampleroot),
                'seedgen':
                getattr(lib.seedgens, modules['seedgen'])(self),
                'sigproc':
                getattr(lib.sigprocs, modules['sigproc'])(
                    self, pyo.Input(), args.rulesfile),
                'chooser':
                getattr(lib.choosers, modules['chooser'])(self),
                'modulator':
                getattr(lib.modulators, modules['modulator'])(self),
                'oscproc': OSCProc(args.oscport),
                'midiproc': MidiProc()
            }

    def start(self):
        for name, module in self.modules.items():
            if isinstance(module, HansModule):
                self.init_module(name)

    def init_module(self, name):
        self.modules[name].init()

    def get_module(self, name):
        return self.modules[str(name)]

    def get_sample_categories(self):
        return self.get_module('samplebank').get_categories()

    def get_effect_types(self):
        return self.get_module('modulator').get_effect_types()


class MidiProc:
    def __init__(self):
        self.rawm = pyo.RawMidi(handle_midievent)
        self.trigger_notes = {}
        # accented bass drum
        for i in (35, 36):
            self.add_trigger(i, 64, 0.5)
        # accented snare
        for i in (38, 40):
            self.add_trigger(i, 70, 0.25)
        # accented toms
        for i in (41, 45, 48, 50):
            self.add_trigger(i, 70, 0.15)
        # accented cymbals
        for i in (49, 51, 55, 57, 59):
            self.add_trigger(i, 70, 0.1)

    def add_trigger(self, note, velocity, limit):
        self.trigger_notes[note] = {'velocity': velocity,
                                    'limit': limit}


def handle_midievent(status, note, velocity):
    # filter note-on messages
    if 144 <= status <= 159:
        try:
            midiproc = hans.get_module('midiproc')
            if velocity > midiproc.trigger_notes[note]['velocity'] and \
               random.random() < midiproc.trigger_notes[note]['limit']:
                hans.get_module('modulator').execute()
        except KeyError:
            pass


class OSCProc:
    def __init__(self, port=5005):
        self.receiver = pyo.OscDataReceive(port, '/hans/*', handle_osc)


def handle_osc(address, *args):
    for type in ['midi', 'ctrl', 'cmd']:
        if type in address:
            globals()['handle_osc_%s' % type](address, *args)


def handle_osc_midi(address, *args):
    data = args[0]
    midi = (data[1], data[2], data[3])
    handle_midievent(*midi)


def handle_osc_ctrl(address, *args):
    param = address.split('/')[-1]
    sigproc = hans.get_module('sigproc')
    if param in sigproc.analysers:
        sigproc.set_inputlim(param, args[0])


def handle_osc_cmd(address, *args):
    if 'samplereload' in address:
        hans.get_module('chooser').reload_samples()
    elif 'rulesreload' in address:
        hans.get_module('sigproc').set_rules_toggle_levels()
    elif 'solo' in address:
        threading.Thread(target=doTheWookieeBoogie).start()


def doTheWookieeBoogie():
    for _ in range(random.randrange(42, 65)):
        handle_midievent(145, 36, 125)
        time.sleep(0.07 + random.random()/4)


def hansstopit(signum, frame):
    server.deactivateMidi()
    hans.get_module('sigproc').terminate()
    server.stop()
    time.sleep(0.2)
    print()
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HANS Server')
    parser.add_argument('-o', '--oscport',
                        help='HANS server OSC port',
                        default=5005,
                        type=int)
    parser.add_argument('-m', '--midi',
                        help='Input MIDI channel number',
                        default=None,
                        type=int)
    parser.add_argument('-s', '--sampleroot',
                        help='Path of samples root folder',
                        default='./samples/')
    parser.add_argument('-r', '--rulesfile',
                        help='File containing AI rules and toggle levels',
                        default='hans.rules')
    parser.add_argument('-c', '--configfile',
                        help='HANS config file',
                        default='hans-config.json')
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose mode',
                        action='store_true')
    args = parser.parse_args()

    if int(''.join(map(str, pyo.getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install "
                          "to version 0.7.6 or later.")

    if args.midi:
        midi_id = args.midi
    else:
        pyo.pm_list_devices()
        midi_id = -1
        while (midi_id > pyo.pm_count_devices()-1 and midi_id != 99) or midi_id < 0:
            midi_id = eval(input("Please select input ID [99 for all]: "))

    server_args = {'duplex': 1, 'ichnls': 1}
    if not sys.platform.startswith('win'):
        server_args.update({'audio': 'jack', 'jackname': 'HANS'})
    server = pyo.Server(**server_args)
    server.setMidiInputDevice(midi_id)
    if args.verbose:
        server.setVerbosity(8)
    server.boot()

    hans = HansMain(args)
    hans.start()

    server.start()

    signal.signal(signal.SIGINT, hansstopit)

    while True:
        time.sleep(2)
