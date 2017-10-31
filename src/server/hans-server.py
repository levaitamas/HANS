#!/usr/bin/env python
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
try:
    import pyo
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
import SocketServer
import argparse
import fnmatch
import logging
import os
import sys
import signal
import random
import threading
import time


class SeedGen:
    def __init__(self):
        self.output = self.execute()

    def execute(self):
        self.output = int(random.random() * 13579)


class Sample(object):
    __slots__ = ['path', 'category', 'audio', 'audio_rate']
    def __init__(self, path, category=None):
        self.path = path
        self.category = category or os.path.basename(os.path.dirname(path))
        self.audio = pyo.SndTable(path)
        self.audio_rate = self.audio.getRate()

    def __str__(self):
        return "{'Path': '%s', 'Category': '%s'}" \
            % (self.path.split(os.sep)[-1], self.category)


class Chooser:
    def __init__(self, seed_gen, sigproc,
                 sample_root='.', enable_ai=True):
        self.sigproc = sigproc
        self.seedgen = seed_gen
        self.sample_root = sample_root
        self.samples =  { 'Human': [], 'Machine': [], 'Music': [],
                          'Nature': [], 'Beep': [], 'Other': []}
        self.num_of_samples = 0
        self.enable_ai = enable_ai
        self.output = None
        self.set_sample_root(sample_root)

    def execute(self):
        self.seedgen.execute()
        categories = []
        if self.enable_ai:
            for category in self.sigproc.output2:
                if self.sigproc.output2[category]:
                    categories.append(category)
            if categories:
                cat = random.choice(categories)
                self.output = self.samples[cat][
                            (self.seedgen.output % len(self.samples[cat])-1)+1]
            else:
                self.output = None
        else:
            self.output = self.samples[
                random.choice(self.samples)][
                    (self.seedgen.output % self.num_of_samples)+1]
        logging.info(str(self.output) or "{'Path': null, 'Category': null}")

    def calc_num_of_samples(self):
        new_num_of_samples = 0
        for cat, samples in self.samples.iteritems():
            new_num_of_samples += len(samples)
        self.num_of_samples = new_num_of_samples
        if self.num_of_samples < 1:
            raise Exception("No samples are available!")

    def set_sample_root(self, path):
        self.samples =  { 'Human': [], 'Machine': [], 'Music': [],
                          'Nature': [], 'Beep': [], 'Other': []}
        if os.path.isdir(path):
            self.sample_root = path
            self.load_samples(path)

    def load_samples(self, folder):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.aiff'):
                path = os.path.join(root, filename)
                self.samples[os.path.basename(root)].append(Sample(path))
        self.calc_num_of_samples()

    def toggle_ai(self, state):
        self.enable_ai = state


class SigProc:
    class Rule:
        def __init__(self, active, inactive, weight):
            self.active = active
            self.inactive = inactive
            self.weight = weight

        def __str__(self):
            return "{'Active': '%s'," \
                   "'Inactive': '%s'," \
                   "'Weight': '%s'}" \
                   % (self.active, self.inactive, self.weight)

    def __init__(self, audioin, modulator=None):
        self.yin = pyo.Yin(audioin)
        self.cen = pyo.Centroid(audioin)
        self.rms = pyo.Follower(audioin)
        self.amp = pyo.PeakAmp(audioin)
        self.yinlim = 400
        self.cenlim = 6000
        self.rmslim = 0.6
        self.amplim = 0.8
        self.inputlist = {}
        self.outputlist = {}
        self.rulelist = []
        self.output = {}
        self.output2 = {}
        self.set_inputlist()
        self.set_outputlist()
        self.set_rules()
        self._terminate = False
        self.modulator = None
        if modulator:
            self.set_modulator(modulator)

    def set_modulator(self, modulator):
        self.modulator = modulator
        threading.Thread(target=self.run).start()

    def run(self):
        while not self._terminate:
            self.execute()
            time.sleep(0.5)
            self.modulator.set_effects(self.output)

    def execute(self):
        self.set_inputlist()
        self.calcout()
        self.output = {
            'Volume': self.toggle(self.outputlist["vol"], 0.2),
            'Volume-param': self.denorm(self.outputlist["vol"], 0.4, 1.0),
            'Speed': self.toggle(self.outputlist["spe"], 0.6),
            'Speed-param': self.denorm(self.outputlist["spe"], 0.4, 1.6),
            'Distortion': self.toggle(self.outputlist["dis"], 0.4),
            'Distortion-param': self.denorm(self.outputlist["dis"], 0.4, 1.0),
            'Chorus': self.toggle(self.outputlist["cho"], 0.4),
            'Chorus-param': self.denorm(self.outputlist["cho"], 1.0, 4.0),
            'Reverb': self.toggle(self.outputlist["rev"], 0.4),
            'Reverb-param': self.denorm(self.outputlist["rev"], 0.0, 0.6),
        }

        self.output2 = {
            'Human': self.toggle(self.outputlist["Human"], 0.25),
            'Machine': self.toggle(self.outputlist["Machine"], 0.48),
            'Music': self.toggle(self.outputlist["Music"], 0.5),
            'Nature': self.toggle(self.outputlist["Nature"], 0.42),
            'Beep': self.toggle(self.outputlist["Beep"], 0.52),
            'Other': self.toggle(self.outputlist["Other"], 0.5),
        }

        logging.info("[%s,%s,%s]" % (self.inputlist, self.output, self.output2))

    def set_inputlist(self):
        self.inputlist = {
            'yin': self.norm(self.yin.get(), 0, self.yinlim),
            'cen': self.norm(self.cen.get(), 0, self.cenlim),
            'rms': self.norm(self.rms.get(), 0, self.rmslim),
            'amp': self.norm(self.amp.get(), 0, self.amplim),
        }

    def set_imputlims(self, yinlim, cenlim, rmslim, amplim):
        self.yinlim = yinlim
        self.cenlim = cenlim
        self.rmslim = rmslim
        self.amplim = amplim

    def set_rules(self):
        self.rulelist = []
        for i in xrange(1, 3):
            self.rulelist.append(self.Rule("vol%s" % id, "vol", 1.0/i))
            self.rulelist.append(self.Rule("spe%s" % id, "spe", 1.0/i))
            self.rulelist.append(self.Rule("dis%s" % id, "dis", 1.0/i))
            self.rulelist.append(self.Rule("cho%s" % id, "cho", 1.0/i))
            self.rulelist.append(self.Rule("rev%s" % id, "rev", 1.0/i))

        self.rulelist.append(self.Rule("yin", "spe", 2.00))
        self.rulelist.append(self.Rule("yin", "dis", 0.70))
        self.rulelist.append(self.Rule("yin", "cho", 0.95))
        self.rulelist.append(self.Rule("yin", "rev", 0.95))

        self.rulelist.append(self.Rule("cen", "vol", 0.90))
        self.rulelist.append(self.Rule("cen", "spe", 0.90))
        self.rulelist.append(self.Rule("cen", "dis", 0.90))
        self.rulelist.append(self.Rule("cen", "cho", 0.90))
        self.rulelist.append(self.Rule("cen", "rev", 0.95))

        self.rulelist.append(self.Rule("rms", "vol", 1.00))
        self.rulelist.append(self.Rule("rms", "dis", 0.8))
        self.rulelist.append(self.Rule("rms", "cho", 0.8))
        self.rulelist.append(self.Rule("rms", "rev", 0.6))

        self.rulelist.append(self.Rule("amp", "vol", 1.00))
        self.rulelist.append(self.Rule("amp", "spe", 0.95))
        self.rulelist.append(self.Rule("amp", "dis", 0.8))
        self.rulelist.append(self.Rule("amp", "cho", 0.70))

        self.rulelist.append(self.Rule("amp", "Human", 1.0))
        self.rulelist.append(self.Rule("yin", "Human", 0.7))
        self.rulelist.append(self.Rule("cen", "Human", 0.8))

        self.rulelist.append(self.Rule("amp", "Machine", 0.8))
        self.rulelist.append(self.Rule("yin", "Machine", 0.7))

        self.rulelist.append(self.Rule("amp", "Music", 0.7))
        self.rulelist.append(self.Rule("yin", "Music", 0.7))
        self.rulelist.append(self.Rule("cen", "Music", 0.6))

        self.rulelist.append(self.Rule("amp", "Nature", 0.7))
        self.rulelist.append(self.Rule("cen", "Nature", 0.85))

        self.rulelist.append(self.Rule("amp", "Beep", 0.7))
        self.rulelist.append(self.Rule("yin", "Beep", 1.0))

        self.rulelist.append(self.Rule("cen", "Other", 0.7))
        self.rulelist.append(self.Rule("amp", "Other", 0.7))
        self.rulelist.append(self.Rule("yin", "Other", 0.3))

    def set_outputlist(self):
        self.outputlist = {}
        for id in ['', '1', '2']:
            self.outputlist["vol%s" % id] = 0
            self.outputlist["spe%s" % id] = 0
            self.outputlist["dis%s" % id] = 0
            self.outputlist["cho%s" % id] = 0
            self.outputlist["rev%s" % id] = 0
        self.outputlist["Other"] = 0
        self.outputlist["Music"] = 0
        self.outputlist["Human"] = 0
        self.outputlist["Nature"] = 0
        self.outputlist["Beep"] = 0
        self.outputlist["Machine"] = 0

    def calcout(self):
        for output_name, output_value in self.outputlist.iteritems():
            templist = []
            for rule in self.rulelist:
                if output_name == rule.inactive:
                    for name, value in self.inputlist.iteritems():
                        if name == rule.active:
                            templist.append((value, rule.weight))
                    for outputold_name, outputold_value in \
                        self.outputlist.iteritems():
                        if outputold_name == rule.active:
                            templist.append((outputold_value, rule.weight))
            if len(templist) != 0:
                self.outputlist[output_name] = self.calcavg(templist)
                self.aging(output_name)

    def norm(self, variable, min, max):
        if (variable < max) and (variable > min):
            return (variable - min) / (max - min)
        elif variable <= min:
            return 0
        else:
            return 1

    def denorm(self, variable, min, max):
        if variable:
            return variable * (max - min) + min
        return 0

    def toggle(self, variable, limit):
        if variable >= limit:
            return True
        return False

    def aging(self, key):
        if "%s2" % key in self.outputlist:
            self.outputlist["%s2" % key] = 0.5 * self.outputlist[("%s2" % key)]
            self.outputlist["%s1" % key] = self.outputlist[key]

    def calcavg(self, tuplelist):
        numerator = sum([l[0] * l[1] for l in tuplelist])
        denominator = sum([l[1] for l in tuplelist])
        if (denominator != 0):
            return (float(numerator) / float(denominator))
        else:
            return 0


class MidiProc:
    def __init__(self, port=5005):
        self.counter = 0
        self.block = False
        self.rawm = pyo.RawMidi(handle_midievent)
        self.osci=pyo.OscDataReceive(port, "/hans/midi", handle_oscmidi)
    def block_midi(self):
        time.sleep(0.25)
        self.block = False


def handle_oscmidi(address, *args):
    data=args[0]
    handle_midievent(data[1], data[2], data[3])


def handle_midievent(status, note, velocity):
    if midiproc.block or midiproc.counter > 2:
        midiproc.counter = 0
        midiproc.block = True
        threading.Thread(target=midiproc.block_midi).start()
        return
    # filter note-on messages
    if 144 <= status <= 159:
        midiproc.counter += 1
        # filter accented bass drum
        if note in {35, 36} and velocity >= 64:
            if random.random() < 0.5:
                modulator.execute()
        # filter accented snare drum
        elif note in {38, 40} and velocity >= 70:
            if random.random() < 0.25:
                modulator.execute()
        # filter accented toms
        elif note in {41, 45, 48, 50} and velocity >= 70:
            if random.random() < 0.15:
                modulator.execute()
        # filter accented cymbals
        elif note in {49, 51, 55, 57, 59} and velocity >= 70:
            if random.random() < 0.1:
                modulator.execute()


def doTheWookieeBoogie():
    for _ in xrange(random.randrange(42, 65)):
        handle_midievent(145, 36, 125)
        time.sleep(0.07 + random.random()/4)


class Modulator:
    def __init__(self, chooser, enable_ai=True):
        self.chooser = chooser
        self.enable_ai = enable_ai

        # Effect Chain:
        # 'Volume' -> 'Speed' -> 'Distortion'
        # -> 'Chorus' -> 'Reverb' -> 'Pan'

        # Effect parameters:
        # 'Volume-param': between 0 and 1
        # 'Speed-param': 1 - original; 0-1 slow; 1< - fast
        # 'Distortion-param': between 0 and 1
        # 'Chorus-param': between 0 and 5
        # 'Reverb-param': between 0 and 1

        self.effectchain = {'Volume': False, 'Volume-param': 0,
                            'Speed': False, 'Speed-param': 0,
                            'Distortion': False, 'Distortion-param': 0,
                            'Chorus': False, 'Chorus-param': 0,
                            'Reverb': False, 'Reverb-param': 0}

        self.player = pyo.TableRead(pyo.NewTable(0.1), loop=False)
        self.denorm_noise = pyo.Noise(1e-24)
        self.distortion = pyo.Disto(self.player, slope=0.7)
        self.sw_disto = pyo.Interp(self.player, self.distortion,
                                   interp=0)
        self.chorus = pyo.Chorus(self.sw_disto + self.denorm_noise,
                                 bal=0.6)
        self.sw_chorus = pyo.Interp(self.sw_disto, self.chorus,
                                    interp=0)
        self.reverb = pyo.Freeverb(self.sw_chorus + self.denorm_noise,
                                   bal=0.7)
        self.sw_reverb = pyo.Interp(self.sw_chorus, self.reverb,
                                    interp=0)
        self.output = pyo.Pan(self.sw_reverb, outs=2, spread=0.1)
        self.output.out()

    def execute(self):
        self.chooser.execute()
        sample = self.chooser.output
        if sample is None:
            return
        self.player.stop()
        self.player.setTable(sample.audio)
        if self.effectchain['Volume']:
            self.player.setMul(0.001 +
                               self.effectchain['Volume-param'])
        if self.effectchain['Speed']:
            self.player.setFreq(sample.audio_rate *
                                self.effectchain['Speed-param'])
        else:
            self.player.setFreq(sample.audio_rate)
        if self.effectchain['Distortion']:
            self.sw_disto.interp = 1
        else:
            self.sw_disto.interp = 0
        if self.effectchain['Chorus']:
            self.sw_chorus.interp = 1
        else:
            self.sw_chorus.interp = 0
        if self.effectchain['Reverb']:
            self.sw_reverb.interp = 1
        else:
            self.sw_reverb.interp = 0
        self.output.setPan(random.choice([0.02, 0.25, 0.5, 0.75, 0.98]))
        self.player.play()


    def set_effects(self, new_setup):
        if self.enable_ai:
            self.effectchain = new_setup
            self.distortion.setDrive(self.effectchain['Distortion-param'])
            self.chorus.reset()
            self.chorus.setDepth(self.effectchain['Chorus-param'])
            self.reverb.reset()
            self.reverb.setSize(self.effectchain['Reverb-param'])

    def toggle_effect(self, name, state):
        for key in self.effectchain.keys():
            if key == name:
                self.effectchain[key] = state

    def toggle_ai(self, state):
        self.enable_ai = state


class NetConHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        if data == 'solo':
            threading.Thread(target=doTheWookieeBoogie).start()
            logging.info('\'SOLO request\'')
        elif data == 'samplereload':
            chooser.set_sample_root(chooser.sample_root)
        elif data.startswith("{'amp':"):
            limits = eval(data)
            sigproc.set_imputlims(limits['yin'], limits['cen'],
                                  limits['rms'], limits['amp'])


class ConnectionManager():
    def __init__(self, host="localhost", port=9999):
        self.port = port
        self.host = host
        self.server = SocketServer.UDPServer((self.host, self.port),
                                             NetConHandler)


def hansstopit(signum, frame):
    server.deactivateMidi()
    sigproc._terminate = True
    time.sleep(0.5)
    server.stop()
    time.sleep(0.2)
    conmanager.server.server_close()
    print(' ')
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HANS Server')
    parser.add_argument('-H', '--host',
                        help='HANS server IP adddress or domain name',
                        default='0.0.0.0')
    parser.add_argument('-p', '--port',
                        help='HANS server port',
                        default='9999',
                        type=int)
    parser.add_argument('-o', '--ocsport',
                        help='HANS server OSC port',
                        default='5005',
                        type=int)
    parser.add_argument('-m', '--midi',
                        help='Input MIDI channel number',
                        default=None,
                        type=int)
    parser.add_argument('-s', '--sampleroot',
                        help='Path of samples root folder',
                        default='./samples/')
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose mode',
                        action='store_true')
    args = parser.parse_args()

    if int(''.join(map(str, pyo.getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")

    if sys.platform.startswith("win"):
        server = pyo.Server(duplex=1, ichnls=1)
    else:
        server = pyo.Server(duplex=1, audio='jack', jackname='HANS', ichnls=1)

    if args.verbose:
        # server.setVerbosity(8)
        logging.basicConfig(filename='hans-server.log',
                            format="{'Timestamp': '%(asctime)s', 'Message': %(message)s},",
                            datefmt='%Y-%m-%d-%H-%M-%S',
                            level=logging.INFO)

    if args.midi:
        server.setMidiInputDevice(args.midi)
    else:
        pyo.pm_list_devices()
        inid = -1
        while (inid > pyo.pm_count_devices()-1 and inid != 99) or inid < 0:
            inid = input("Please select input ID [99 for all]: ")
            server.setMidiInputDevice(inid)
    server.boot()
    server.start()

    sigproc = SigProc(pyo.Input())
    seedgen = SeedGen()
    chooser = Chooser(seedgen, sigproc, sample_root=args.sampleroot)
    modulator = Modulator(chooser)
    sigproc.set_modulator(modulator)
    conmanager = ConnectionManager(args.host, args.port)
    midiproc = MidiProc(args.oscport)

    signal.signal(signal.SIGINT, hansstopit)

    logging.info('\'HANS-SERVER started\'')

    conmanager.server.serve_forever(1)
