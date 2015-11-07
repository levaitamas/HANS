#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
"""
from pyo import *
import fnmatch
import os
import sys
import random


class SeedGen:
    def __init__(self):
        self.output = self.execute()

    def execute(self):
        self.output = random.randint(1, 102334155)


class Chooser:
    def __init__(self, seed_gen, sample_path='.'):
        assert seed_gen
        self.seedgen = seed_gen
        self.sample_path = sample_path
        self.samples = []
        self.reload_samples()
        self.output = ''
        self.execute()

    def execute(self):
        self.seedgen.execute()
        self.output = self.samples[(self.seedgen.output %
                                    self.number_of_samples)]

    def reload_samples(self):
        self.samples = []
        for root, dirnames, filenames in os.walk(self.sample_path):
            for filename in fnmatch.filter(filenames, '*.aiff'):
                self.samples.append(os.path.join(root, filename))
        self.number_of_samples = len(self.samples)


class MidiProc:
    def __init__(self):
        self.rawm = RawMidi(handle_midievent)

    def execute(self):
        pass


def handle_midievent(status, note, velocity):
    if status == 153 and note == 36 and velocity >= 63:
        modulatr.execute()


class Modulator:
    def __init__(self, chooser):
        assert chooser
        self.chooser = chooser
        self.output = SfPlayer(self.chooser.output, loop=False)

    def execute(self):
        if random.random() < 0.6:
            self.chooser.execute()
            self.output.setSound(self.chooser.output)
            self.output.out()


if __name__ == "__main__":
    # check pyo version because RawMidi is supported only since version 0.7.6
    if int(''.join(map(str, getVersion()))) < 76:
        sys.exit(1)

    # setup server
    if sys.platform.startswith("win"):
        server = Server().boot()
    else:
        server = Server(audio='jack', jackname='HANS').boot()

    # enable debug info
    server.setVerbosity(8)

    # set MIDI input
    pm_list_devices()
    inid = -1
    while (inid > pm_count_devices()-1 and inid != 99) or inid < 0:
        inid = input("Please select input ID [99 for all]: ")
    server.setMidiInputDevice(inid)

    server.start()

    # initialise components
    seedgen = SeedGen()
    chooser = Chooser(seedgen)
    # rtsigproc = rtsigproc.RTSigProc()
    midiproc = MidiProc()
    modulatr = Modulator(chooser)
    # mixer = Mixer(modulatr)

    # start GUI to prevent main thread termination
    server.gui(locals())
