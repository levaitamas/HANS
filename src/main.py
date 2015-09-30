#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamas Levai <levait@tmit.bme.hu>


"""

import threading
import pyo

import chooser
import midiproc
import mixer
import modulator
import rtsigproc
import seedgen

if __name__ == "__main__":
    # start pyo
    server = pyo.Server()
    server.boot()
    server.start()

    # initialise components
    seedgen = seedgen.SeedGen()
    chooser = chooser.Chooser(seedgen)
    rtsigproc = rtsigproc.RTSigProc()
    midiproc = midiproc.MidiProc()
    modulator = modulator.Modulator(midiproc, rtsigproc, chooser)
    mixer = mixer.Mixer(modulator)

    # start threads for chooser, modulator, midiproc, sigproc - TODO

    # start waiting for midiproc events (maybe in a separate thread) - TODO
    #  if midiproc event occurs, alert components - TODO

    # create some ui - TODO
