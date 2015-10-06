#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
"""
from pyo import *
import sys

import midiproc

if __name__ == "__main__":
    # setup server
    if sys.platform.startswith("win"):
        server = Server().boot()
    else:
        server = Server(audio='jack', jackname='pyo').boot()

    # enable debug info
    server.setVerbosity(8)

    # set MIDI input
    pm_list_devices()
    inid = -1
    while (inid > pm_count_devices()-1 and inid != 99) or inid < 0:
        inid = input("Please select input ID: ")
    server.setMidiInputDevice(inid)

    server.start()

    # initialise components
    # seedgen = seedgen.SeedGen()
    # chooser = chooser.Chooser(seedgen)
    # rtsigproc = rtsigproc.RTSigProc()
    midiproc = midiproc.MidiProc()
    # modulator = modulator.Modulator(midiproc, rtsigproc, chooser)
    # mixer = mixer.Mixer(modulator)

    # TODOs:
    # - start threads for chooser, modulator, midiproc, sigproc
    # - start waiting for midiproc events (maybe in a separate thread)
    #   or create some function to call if specific midi event occurs

    server.gui(locals())
