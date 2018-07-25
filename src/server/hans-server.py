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
try:
    import pyo
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
from collections import namedtuple
from pathlib import Path
import argparse
import logging
import random
import re
import signal
import sys
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
        self.path = Path(path)
        self.category = category or self.path.parent.name
        self.audio = pyo.SndTable(str(self.path))
        self.audio_rate = self.audio.getRate()

    def __str__(self):
        return "{'Path': '%s', 'Category': '%s'}" \
            % (self.path.name, self.category)


class SampleBank(object):
    def __init__(self, sample_root='.'):
        self.sample_root = sample_root
        self.reload_samples()

    def reload_samples(self):
        self.init_samples()
        self.load_samples(self.sample_root)

    def init_samples(self):
        self.samples = {}
        for cat in ['Human', 'Machine', 'Music',
                    'Nature', 'Beep', 'Other']:
            self.samples[cat] = []

    def load_samples(self, sample_root='.'):
        if Path(sample_root).is_dir():
            for sample in Path(sample_root).glob('**/*.aiff'):
                self.samples[sample.parent.name].append(Sample(sample))
        self.check_num_of_samples()

    def check_num_of_samples(self):
        num_of_samples = sum([len(s) for c, s in self.samples.items()])
        if num_of_samples < 1:
            raise Exception("No samples are available!")


class Chooser:
    def __init__(self, seed_gen, sigproc, sample_bank, enable_ai=True):
        self.sigproc = sigproc
        self.seedgen = seed_gen
        self.enable_ai = enable_ai
        self.sample_bank = sample_bank

    def execute(self):
        self.seedgen.execute()
        if self.enable_ai:
            categories = [c
                          for c in self.sigproc.output2
                          if self.sigproc.output2[c]]
        else:
            categories = self.sample_bank.samples.keys()
        try:
            category = random.choice(categories)
            idx = self.seedgen.output % len(self.sample_bank.samples[category])
            self.output = self.sample_bank.samples[category][idx]
        except:
            self.output = None
        logging.info(str(self.output) or "{'Path': null, 'Category': null}")

    def reload_samples(self):
        self.sample_bank.reload_samples()

    def set_sample_root(self, sample_root):
        self.sample_bank = SampleBank(sample_root)

    def toggle_ai(self, state):
        self.enable_ai = state


class SigProc:
    Rule = namedtuple('Rule', ['active', 'inactive', 'weight'])
    Analyser = namedtuple('Analyser', ['module', 'limit'])
    sample_categories = ['Human', 'Machine', 'Music',
                         'Nature', 'Beep', 'Other']
    effect_types = ['Volume', 'Speed', 'Distortion', 'Chorus', 'Reverb']

    def __init__(self, audioin, rules_file, modulator=None):
        self.set_rules_toggle_levels(rules_file)
        self.init_analysers(audioin)
        self.set_inputlist()
        self.init_outputlist()
        self.update_interval = 0.5
        self._terminate = False
        if modulator:
            self.set_modulator(modulator)

    def set_modulator(self, modulator):
        self.modulator = modulator
        threading.Thread(target=self.run).start()

    def init_analysers(self, audioin):
        self.analysers = {'yin': self.Analyser(pyo.Yin(audioin), 400),
                          'cen': self.Analyser(pyo.Centroid(audioin), 6000),
                          'rms': self.Analyser(pyo.Follower(audioin), 0.6),
                          'amp': self.Analyser(pyo.PeakAmp(audioin), 0.8)}

    def run(self):
        while not self._terminate:
            self.execute()
            time.sleep(self.update_interval)
            if self.modulator.enable_ai:
                self.modulator.set_effects(self.output)

    def execute(self):
        self.set_inputlist()
        self.calcout()
        self.output = {
            'Volume-param': self.denorm(self.outputlist['Volume'], 0.4, 1.0),
            'Speed-param': self.denorm(self.outputlist['Speed'], 0.4, 1.6),
            'Distortion-param': self.denorm(self.outputlist['Distortion'], 0.4, 1.0),
            'Chorus-param': self.denorm(self.outputlist['Chorus'], 1.0, 4.0),
            'Reverb-param': self.denorm(self.outputlist['Reverb'], 0.0, 0.6),
        }
        self.output.update({cat: self.toggle(self.outputlist[cat],
                                             self.toggle_levels[cat])
                            for cat in self.effect_types})
        self.output2 = {cat: self.toggle(self.outputlist[cat],
                                         self.toggle_levels[cat])
                        for cat in self.sample_categories}
        logging.info("[%s,%s,%s]" % (self.inputlist,
                                     self.output,
                                     self.output2))

    def set_inputlist(self):
        self.inputlist = {m: self.norm(self.analysers[m].module.get(),
                                       0, self.analysers[m].limit)
                          for m in self.analysers}

    def set_inputlim(self, name, value):
        setattr(self, '%slim' % name, value)

    def set_rules_toggle_levels(self, rules_file=None):
        if rules_file:
            self.rules_file = rules_file
        self.rulelist = [self.Rule("%s%s" % (cat, i), cat, 1/i)
                         for cat in self.effect_types
                         for i in range(1, 3)]
        self.load_rules(self.rules_file)
        self.toggle_levels = {}
        self.load_toggle_levels(self.rules_file)

    def load_rules(self, rules_file):
        # active | inactive : weight
        regex = "^\s*(\w+)\s*\|\s*(\w+)\s*\:\s*([-+]?\d*\.\d+|\d)"
        pattern = re.compile(regex)
        with open(rules_file) as rfile:
            for line in rfile:
                caps = re.findall(pattern, line)
                for cap in caps:
                    new_rule = self.Rule(cap[0], cap[1], float(cap[2]))
                    self.rulelist.append(new_rule)

    def load_toggle_levels(self, rules_file):
        # category : weight
        regex = "^\s*(\w+)\s*\:\s*([-+]?\d*\.\d+|\d)"
        pattern = re.compile(regex)
        with open(rules_file) as rfile:
            for line in rfile:
                caps = re.findall(pattern, line)
                for cap in caps:
                    self.toggle_levels[cap[0]] = float(cap[1])

    def init_outputlist(self):
        self.outputlist = {cat: 0 for cat in self.sample_categories}
        self.outputlist.update({'%s%s' % (c, i): 0
                                for c in self.effect_types
                                for i in ['', '1', '2']})

    def calcout(self):
        for output_name in self.outputlist:
            tmplist = []
            for rule in self.rulelist:
                if output_name == rule.inactive:
                    tmplist += [(self.inputlist[in_name], rule.weight)
                                for in_name in self.inputlist
                                if in_name == rule.active]
                    tmplist += [(self.outputlist[out_name], rule.weight)
                                for out_name in self.outputlist
                                if out_name == rule.active]
            if tmplist:
                self.outputlist[output_name] = self.calcavg(tmplist)
                self.age(output_name)

    def norm(self, variable, min, max):
        if min < variable < max:
            return (variable - min) / (max - min)
        elif variable <= min:
            return 0
        else:
            return 1

    def denorm(self, variable, min, max):
        if variable:
            return variable * (max - min) + min
        return 0

    def calcavg(self, tuplelist):
        numerator = sum([l[0] * l[1] for l in tuplelist])
        denominator = sum([l[1] for l in tuplelist])
        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0

    def age(self, key):
        try:
            self.outputlist["%s2" % key] = 0.5 * self.outputlist["%s1" % key]
            self.outputlist["%s1" % key] = self.outputlist[key]
        except KeyError:
            pass

    def toggle(self, variable, limit):
        return variable >= limit


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
            if velocity > midiproc.trigger_notes[note]['velocity'] and \
               random.random() < midiproc.trigger_notes[note]['limit']:
                modulator.execute()
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
    if param in sigproc.analysers:
        sigproc.set_inputlim(param, args[0])


def handle_osc_cmd(address, *args):
    if 'samplereload' in address:
        chooser.reload_samples()
    elif 'rulesreload' in address:
        sigproc.set_rules_toggle_levels()
    elif 'solo' in address:
        threading.Thread(target=doTheWookieeBoogie).start()
        logging.info('\'SOLO request\'')


def doTheWookieeBoogie():
    for _ in range(random.randrange(42, 65)):
        handle_midievent(145, 36, 125)
        time.sleep(0.07 + random.random()/4)


class Modulator:
    effect_types = ['Volume', 'Speed', 'Distortion', 'Chorus', 'Reverb']
    pan_positions = [0.02, 0.25, 0.5, 0.75, 0.98]

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

        self.effectchain = {}
        for e in self.effect_types:
            self.effectchain[e] = False
            self.effectchain['%s-param' % e] = 0

        self.player = pyo.TableRead(pyo.NewTable(0.1), loop=False)
        denorm_noise = pyo.Noise(1e-24)
        self.distortion = pyo.Disto(self.player, slope=0.7)
        self.sw_distortion = pyo.Interp(self.player, self.distortion, interp=0)
        self.chorus = pyo.Chorus(self.sw_distortion + denorm_noise, bal=0.6)
        self.sw_chorus = pyo.Interp(self.sw_distortion, self.chorus, interp=0)
        self.reverb = pyo.Freeverb(self.sw_chorus + denorm_noise, bal=0.7)
        self.sw_reverb = pyo.Interp(self.sw_chorus, self.reverb, interp=0)
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
            self.player.setMul(self.effectchain['Volume-param'])
        freq = {True: self.effectchain['Speed-param'],
                False: 1}[self.effectchain['Speed']] * sample.audio_rate
        self.player.setFreq(freq)
        for effect in ['Distortion', 'Chorus', 'Reverb']:
            sw = getattr(self, 'sw_%s' % effect.lower())
            sw.interp = {True: 1, False: 0}[self.effectchain[effect]]

        self.output.setPan(random.choice(self.pan_positions))
        self.player.play()

    def set_effects(self, new_setup):
        self.effectchain = new_setup
        self.distortion.setDrive(self.effectchain['Distortion-param'])
        self.chorus.reset()
        self.chorus.setDepth(self.effectchain['Chorus-param'])
        self.reverb.reset()
        self.reverb.setSize(self.effectchain['Reverb-param'])

    def toggle_effect(self, name, state):
        try:
            self.effectchain[name] = state
        except KeyError:
            pass

    def toggle_ai(self, state):
        self.enable_ai = state


def hansstopit(signum, frame):
    server.deactivateMidi()
    sigproc._terminate = True
    time.sleep(sigproc.update_interval)
    server.stop()
    time.sleep(0.2)
    print(' ')
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
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose mode',
                        action='store_true')
    parser.add_argument('-l', '--logfile',
                        help='Logfile',
                        default='hans-server.log')
    args = parser.parse_args()

    if int(''.join(map(str, pyo.getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install "
                          "to version 0.7.6 or later.")
    if args.verbose:
        # server.setVerbosity(8)
        logging.basicConfig(filename=args.logfile,
                            format="{'Timestamp': '%(asctime)s', 'Message': %(message)s},",
                            datefmt='%Y-%m-%d-%H-%M-%S',
                            level=logging.INFO)
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
    server.boot()

    samplebank = SampleBank(sample_root=args.sampleroot)
    seedgen = SeedGen()
    sigproc = SigProc(pyo.Input(), args.rulesfile)
    chooser = Chooser(seedgen, sigproc, sample_bank=samplebank)
    modulator = Modulator(chooser)
    sigproc.set_modulator(modulator)
    oscproc = OSCProc(args.oscport)
    midiproc = MidiProc()

    server.start()

    signal.signal(signal.SIGINT, hansstopit)

    logging.info('\'HANS-SERVER started\'')

    while True:
        time.sleep(2)
