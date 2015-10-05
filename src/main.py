#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamas Levai <levait@tmit.bme.hu>


"""

import threading
import time
from pyo import *
from collections import deque


class MidiProc:

    def midievent(status, note, velocity):
        #if status == 153 && note == 36 && velocity >= 63
        print status, note, velocity

    def printnotes(self, notes):
        while(1):
            #notes = Notein(poly=10, scale=1, mul=.5)
            print notes['velocity'], notes['pitch']
            time.sleep(1)
                     
    def __init__(self):
        #self.output = deque([])
        #self.rawm = RawMidi(self.midievent)           
        #notes = Notein()#poly=10, scale=1, mul=.5)      
        #threading.Thread(target = self.printnotes(self.notes)).start()
        pass

    def execute(self):
        pass

def printnotes(notes):
    while(1):
        #notes = Notein(poly=10, scale=1, mul=.5)
        print notes['velocity'], notes['pitch']
        time.sleep(1)

if __name__ == "__main__":

    # initialise components
    #seedgen = seedgen.SeedGen()
    #chooser = chooser.Chooser(seedgen)
    #rtsigproc = rtsigproc.RTSigProc()
    midiproc = MidiProc()#midiproc.MidiProc(server)
    #modulator = modulator.Modulator(midiproc, rtsigproc, chooser)
    #mixer = mixer.Mixer(modulator)    

    # start threads for chooser, modulator, midiproc, sigproc - TODO

    # start waiting for midiproc events (maybe in a separate thread) - TODO
    #  if midiproc event occurs, alert components - TODO

    # create some ui - TODO
    # setup server
    server = Server().boot()
    
    # set MIDI input
    pm_list_devices()
    #inid = input("Please select input ID!\n") # later check validity: names, indexes = pm_get_input_devices()
    server.setMidiInputDevice(99) # opens all devices #(int(inid)) # enter your device number
    server.start()
    notes = Notein()#poly=10, scale=1, mul=.5)
    #threading.Thread(target = printnotes(notes)).start()
    #while(1):
    #    #notes = Notein(poly=10, scale=1, mul=.5)
    #    print MidiAdsr(self.notes['velocity']), MToF(self.notes['pitch'])
    #    time.sleep(1)
    # Pitch
    pitch = MToF(notes['pitch'])
    # ADSR
    amp = MidiAdsr(notes['velocity'])
    # Table
    wave = LogTable()#SquareTable()
    # Osc
    osc = Osc(wave, freq=pitch, mul=amp)
    verb = Freeverb(osc).out()
    ### Go
    osc.out()
    #s.gui(locals()) # Prevents immediate script termination.
    #server.stop() 

