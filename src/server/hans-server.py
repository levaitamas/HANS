#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS SERVER

Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
"""
try:
    from pyo import *
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
import SocketServer
import argparse
import fnmatch
import os
import sys
import random
import threading
import time


class SeedGen:
    def __init__(self):
        self.output = self.execute()

    def execute(self):
        self.output = random.randrange(1, 102334156)


class Sample:
    def __init__(self, path, category=None):
        assert path
        self.path = path
        self.category = category or os.path.basename(os.path.dirname(path))

    def __repr__(self):
        return ("\n" + self.path.split(os.sep)[-1] +
                " [" + str(self.category) + "]")


class SigProc:
    class Variable:
        def __init__(self, name, value):
            self.name = name
            self.value = value

        def __repr__(self):
            return "\n" + str(self.name) + ": " + str(self.value)

    class Rule:
        def __init__(self, active, inactive, weight):
            self.active = active
            self.inactive = inactive
            self.weight = weight

        def __repr__(self):
            return ("\n" + str(self.active) +
                    " effects " + str(self.inactive) +
                    " with " + str(self.weight))

    class WeightedValue:
        def __init__(self, value, weight):
            self.value = value
            self.weight = weight

        def __repr__(self):
            return ("\n" + str(self.value) +
                    " with " + str(self.weight))

    def __init__(self, audioin):
        self.yin = Yin(audioin)
        self.cen = Centroid(audioin)
        self.rms = Follower(audioin)
        self.amp = PeakAmp(audioin)
        self.yinlim = 400
        self.cenlim = 6000
        self.rmslim = 0.6
        self.amplim = 0.8
        self.inputlist = []
        self.outputlist = []
        self.rulelist = []
        self.set_inputs()
        self.set_outputs()
        self.set_rules()
        self.output = {}
        self.output2 = {}

    def execute(self):
        self.set_inputs()
        self.calcout()
        self.output = {
            'Volume': self.limit(self.outputlist[self.get_output("vol")].value, 0.4),
            'Volume-param': self.denorm(self.outputlist[self.get_output("vol")].value, 0.2, 1.0),
            'Speed': self.limit(self.outputlist[self.get_output("spe")].value, 0.6),
            'Speed-param': random.choice([-1, 1]) * self.denorm(self.outputlist[self.get_output("spe")].value, 0.6, 1.4),
            'Distortion': self.limit(self.outputlist[self.get_output("dis")].value, 0.4),
            'Distortion-param': self.denorm(self.outputlist[self.get_output("dis")].value, 0.4, 1.0),
            'Frequency Shifter': self.limit(self.outputlist[self.get_output("fre")].value, 0.6),
            'FS-param': self.denorm(self.outputlist[self.get_output("fre")].value, -2000.0, 8000.0),
            'Chorus': self.limit(self.outputlist[self.get_output("cho")].value, 0.4),
            'Chorus-param': self.denorm(self.outputlist[self.get_output("cho")].value, 1.0, 4.0),
            'Reverb': self.limit(self.outputlist[self.get_output("rev")].value, 0.4),
            'Reverb-param': self.denorm(self.outputlist[self.get_output("rev")].value, 0.0, 0.6)
        }

        self.output2 = {
            'Human': self.limit(self.outputlist[self.get_output("Human")].value, 0.42),
            'Machine': self.limit(self.outputlist[self.get_output("Machine")].value, 0.42),
            'Music': self.limit(self.outputlist[self.get_output("Music")].value, 0.42),
            'Nature': self.limit(self.outputlist[self.get_output("Nature")].value, 0.42),
            'Beep': self.limit(self.outputlist[self.get_output("Beep")].value, 0.42),
            'Other': self.limit(self.outputlist[self.get_output("Other")].value, 0.5),
        }

    def set_inputs(self):
        self.inputlist = []
        self.inputlist.append(self.Variable("yin", self.norm(self.yin.get(), 0, self.yinlim)))
        self.inputlist.append(self.Variable("cen", self.norm(self.cen.get(), 0, self.cenlim)))
        self.inputlist.append(self.Variable("rms", self.norm(self.rms.get(), 0, self.rmslim)))
        self.inputlist.append(self.Variable("amp", self.norm(self.amp.get(), 0, self.amplim)))

    def set_imputlims(self, yinlim, cenlim, rmslim, amplim):
        self.yinlim = yinlim
        self.cenlim = cenlim
        self.rmslim = rmslim
        self.amplim = amplim

    def set_rules(self):
        self.rulelist = []
        for i in xrange(1, 3):
            id = str(i)
            self.rulelist.append(self.Rule("vol"+id, "vol", 1.0/i))
            self.rulelist.append(self.Rule("spe"+id, "spe", 1.0/i))
            self.rulelist.append(self.Rule("dis"+id, "dis", 1.0/i))
            self.rulelist.append(self.Rule("fre"+id, "fre", 1.0/i))
            self.rulelist.append(self.Rule("cho"+id, "cho", 1.0/i))
            self.rulelist.append(self.Rule("rev"+id, "rev", 1.0/i))

        self.rulelist.append(self.Rule("yin", "spe", 2.00))
        self.rulelist.append(self.Rule("yin", "dis", 0.70))
        self.rulelist.append(self.Rule("yin", "fre", 0.60))
        self.rulelist.append(self.Rule("yin", "cho", 0.95))
        self.rulelist.append(self.Rule("yin", "rev", 0.95))

        self.rulelist.append(self.Rule("cen", "vol", 0.90))
        self.rulelist.append(self.Rule("cen", "spe", 0.90))
        self.rulelist.append(self.Rule("cen", "dis", 0.90))
        self.rulelist.append(self.Rule("cen", "fre", 0.50))
        self.rulelist.append(self.Rule("cen", "cho", 0.90))
        self.rulelist.append(self.Rule("cen", "rev", 0.95))

        self.rulelist.append(self.Rule("rms", "vol", 1.00))
        self.rulelist.append(self.Rule("rms", "dis", 0.8))
        self.rulelist.append(self.Rule("rms", "fre", 0.65))
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

        self.rulelist.append(self.Rule("amp", "Nature", 0.7))
        self.rulelist.append(self.Rule("cen", "Nature", 0.85))

        self.rulelist.append(self.Rule("amp", "Beep", 0.7))
        self.rulelist.append(self.Rule("yin", "Beep", 1.0))

        self.rulelist.append(self.Rule("cen", "Other", 0.7))
        self.rulelist.append(self.Rule("amp", "Other", 0.7))
        self.rulelist.append(self.Rule("yin", "Other", 0.3))

    def set_outputs(self):
        self.outputlist = []
        for id in ['', '1', '2']:
            self.outputlist.append(self.Variable("vol"+id, 0))
            self.outputlist.append(self.Variable("spe"+id, 0))
            self.outputlist.append(self.Variable("dis"+id, 0))
            self.outputlist.append(self.Variable("fre"+id, 0))
            self.outputlist.append(self.Variable("cho"+id, 0))
            self.outputlist.append(self.Variable("rev"+id, 0))
        self.outputlist.append(self.Variable("Other", 0))
        self.outputlist.append(self.Variable("Music", 0))
        self.outputlist.append(self.Variable("Human", 0))
        self.outputlist.append(self.Variable("Nature", 0))
        self.outputlist.append(self.Variable("Beep", 0))
        self.outputlist.append(self.Variable("Machine", 0))

    def get_output(self, name):
        for output in self.outputlist:
            if output.name == name:
                return self.outputlist.index(output)
        return None

    def calcout(self):
        templist = []
        for output in self.outputlist:
            for rule in self.rulelist:
                if output.name == rule.inactive:
                    for input in self.inputlist:
                        if input.name == rule.active:
                            templist.append(
                                self.WeightedValue(input.value,
                                                   rule.weight))
                    for outputold in self.outputlist:
                        if outputold.name == rule.active:
                            templist.append(
                                self.WeightedValue(outputold.value,
                                                   rule.weight))
            if len(templist) != 0:
                output.value = self.calcavg(templist)
                self.aging(output)
            templist = []

    def norm(self, variable, min, max):
        if variable < max and variable > min:
            return (variable - min) / (max - min)
        elif variable <= min:
            return 0
        else:
            return 1

    def denorm(self, variable, min, max):
        if variable:
            return variable * (max - min) + min
        return 0

    def limit(self, variable, limit):
        if variable >= limit:
            return 1
        else:
            return 0

    def aging(self, variable):
        for output in self.outputlist:
            if output.name[:-1] == variable.name:
                if output.name[-1:] == "1":
                    output.value = variable.value
                elif output.name[-1:] == "2":
                    output.value = 0.5 * variable.value

    def calcavg(self, sumlist):
        numerator = sum([l.value * l.weight for l in sumlist])
        denominator = sum([l.weight for l in sumlist])
        if (denominator != 0):
            return (float(numerator) / float(denominator))
        else:
            return 0


class Chooser:
    def __init__(self, seed_gen, sigproc,
                 sample_root='.', enable_ai=True):
        assert seed_gen
        assert sigproc
        self.sigproc = sigproc
        self.seedgen = seed_gen
        self.sample_root = sample_root
        self.sample_list = []
        self.num_of_samples = 0
        self.enable_ai = enable_ai
        self.output = None
        self.set_sample_root(sample_root)
        self.execute()

    def execute(self):
        self.seedgen.execute()
        samples = []
        if self.enable_ai:
            if self.num_of_samples > 0:
                for sample in self.sample_list:
                    if sample.category in self.sigproc.output2:
                        # Sample categories: {'Human': 0, 'Machine': 0,
                        # 'Beep': 0, 'Nature': 0, 'Music': 0, 'Other': 0}
                        if self.sigproc.output2[sample.category] == 1:
                            samples.append(sample)
                has_samples = len(samples)
                if has_samples > 0:
                    self.output = samples[(self.seedgen.output % has_samples)]
                else:
                    self.output = None
            else:
                self.output = None
        else:
            if self.num_of_samples > 0:
                self.output = self.sample_list[
                    (self.seedgen.output % self.num_of_samples)]
            else:
                self.output = None

    def set_sample_root(self, path):
        if os.path.isdir(path):
            self.sample_root = path
            self.load_samples_from_folder(path)
            self.sample_list = list(set(self.sample_list))

    def load_samples_from_folder(self, folder):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.aiff'):
                sample_path = os.path.join(root, filename)
                self.sample_list.append(Sample(sample_path))
        self.sample_list = list(set(self.sample_list))
        self.num_of_samples = len(self.sample_list)

    def remove_samples_from_folder(self, folder):
        self.sample_list = [sample for sample in self.sample_list if
                            os.path.dirname(sample.path) != folder]
        self.num_of_samples = len(self.sample_list)

    def toggle_ai(self, state):
        self.enable_ai = state


class MidiProc:
    def __init__(self):
        self.rawm = RawMidi(handle_midievent)


def handle_midievent(status, note, velocity):
    # filter note-on messages
    if 144 <= status <= 159:
        # filter accented bass drum
        if note == 36 and velocity >= 52:
            if random.random() < 0.6:
                modulator.execute()
        # filter accented snare drum
        elif note == 38 or note == 40 and velocity >= 52:
            if random.random() < 0.3:
                modulator.execute()
        # filter accented toms
        elif note == 45 or note == 50 and velocity >= 76:
            if random.random() < 0.2:
                modulator.execute()
        # filter accented ride
        elif note == 59 and velocity >= 64:
            if random.random() < 0.1:
                modulator.execute()
        elif random.random() < 0.042:
            modulator.execute()


def doTheWookieeBoogie():
    for _ in xrange(random.randrange(42, 65)):
        handle_midievent(145, 36, 125)
        time.sleep(0.07 + random.random()/4)


class Modulator:
    def __init__(self, chooser, sigproc, enable_ai=True):
        assert chooser
        assert sigproc
        self.chooser = chooser
        self.sigproc = sigproc
        self.output = None
        self.enable_ai = enable_ai
        # Effect Chain:
        # 'Volume' -> 'Speed' -> 'Distortion'
        # -> 'Frequency Shifter' -> 'Chorus' -> 'Reverb'

        # Effect parameters:
        # 'Volume-param': between 0 and 1
        # 'Speed-param': 1 - original; 0> - reverse; 0-1 slow; 1< - fast
        # 'Distortion-param': between 0 and 1
        # 'FS-param': amount of shifting in Hertz
        # 'Chorus-param': between 0 and 5
        # 'Reverb-param': between 0 and 1

        self.effectchain = {'Volume': 0, 'Volume-param': 0,
                            'Speed': 0, 'Speed-param': 0,
                            'Distortion': 0, 'Distortion-param': 0,
                            'Frequency Shifter': 0, 'FS-param': 0,
                            'Chorus': 0, 'Chorus-param': 0,
                            'Reverb': 0, 'Reverb-param': 0}

    def execute(self):
        if self.enable_ai:
            self.sigproc.execute()
            self.effectchain = self.sigproc.output
            # print datetime.datetime.now()
            # pprint.pprint(self.effectchain)
        self.chooser.execute()
        sample = self.chooser.output
        if sample is None:
            return
        # print sample
        player = SfPlayer(sample.path, loop=False)
        denorm_noise = Noise(1e-24)
        if self.effectchain['Volume']:
            player.setMul(self.effectchain['Volume-param'] or
                          random.random())
        if self.effectchain['Speed']:
            player.setSpeed(self.effectchain['Speed-param'] or
                            (0.5 + random.random()/2))
        if self.effectchain['Distortion']:
            distortion = Disto(player,
                               drive=self.effectchain['Distortion-param'] or
                               random.uniform(0.4, 1),
                               slope=0.7)
        else:
            distortion = player
        if self.effectchain['Frequency Shifter']:
            freqshift = FreqShift(distortion + denorm_noise,
                                  self.effectchain['FS-param'] or
                                  random.random() * 220)
        else:
            freqshift = distortion + denorm_noise
        if self.effectchain['Chorus']:
            chorus = Chorus(freqshift,
                            depth=self.effectchain['Chorus-param'] or
                            random.uniform(1, 5),
                            feedback=random.random(),
                            bal=0.6)
        else:
            chorus = freqshift
        if self.effectchain['Reverb']:
            self.output = Freeverb(chorus,
                                   size=self.effectchain['Reverb-param'] or
                                   random.random(),
                                   damp=random.random(), bal=0.7)
        else:
            self.output = chorus
        if random.random() < 0.5:
            self.output.out()
        else:
            self.output.out(1)

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

    if int(''.join(map(str, getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")

    if sys.platform.startswith("win"):
        server = Server(duplex=1).boot()
    else:
        server = Server(duplex=1, audio='jack', jackname='HANS').boot()

    if args.verbose:
        server.setVerbosity(8)

    if args.midi:
        server.setMidiInputDevice(args.midi)
    else:
        pm_list_devices()
        inid = -1
        while (inid > pm_count_devices()-1 and inid != 99) or inid < 0:
            inid = input("Please select input ID [99 for all]: ")
            server.setMidiInputDevice(inid)
    server.start()

    midiproc = MidiProc()
    sigproc = SigProc(Input())
    seedgen = SeedGen()
    chooser = Chooser(seedgen, sigproc, sample_root=args.sampleroot)
    modulator = Modulator(chooser, sigproc)
    conmanager = ConnectionManager(args.host, args.port)

    conmanager.server.serve_forever()
