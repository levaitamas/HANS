#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL - SERVER

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
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
import time


class Sample:
    def __init__(self, path, category=None):
        assert path
        self.path = path
        self.category = category or os.path.basename(os.path.dirname(path))
        self.audio = SndTable(path, chnl=1)
        self.audio_rate = self.audio.getRate()
        self.player = TableRead(table=self.audio,
                                freq=self.audio_rate,
                                loop=False).stop()


class SamplePlayer:
    def __init__(self, modulator, sample_root='.'):
        self.modulator = modulator
        self.sample_root = sample_root
        self.samples = {}
        self.reset_samples()
        self.selected_kit = ''
        self.mixer = None
        self.set_kit('DK0')
        self.init_mixer()

    def init_mixer(self):
        self.mixer = None
        categories = ['kick', 'snare', 'tom1', 'tom2', 'tom3',
                      'crash', 'ride', 'hho', 'hhc', 'foot']
        self.mixer = Mixer(outs=1, chnls=len(categories))
        for sample in categories:
            sampleH = "%sH" % sample
            if self.samples[sampleH]:
                self.mixer.addInput(sample,
                                    self.samples[sampleH].player)
                self.mixer.setAmp(sample, 0, 0.1)

    def execute(self, pad):
        self.mixer.delInput(pad[:-1])
        self.mixer.addInput(pad[:-1],
                            self.samples[pad].player)
        self.mixer.setAmp(pad[:-1], 0, 0.1)
        self.samples[pad].player.play()
        self.modulator.execute(self.mixer[0])

    def set_kit(self, category):
        self.selected_kit = category
        self.reset_samples()
        self.load_samples(os.path.join(self.sample_root, category))
        self.init_mixer()

    def load_samples(self, folder):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.aiff'):
                path = os.path.join(root, filename)
                self.samples[
                    os.path.basename(filename).split('-')[0]] = Sample(path)

    def reset_samples(self):
        self.samples =  { 'kickL': None, 'kickM': None, 'kickH': None,
                          'snareL': None, 'snareM': None, 'snareH': None,
                          'tom1L': None, 'tom1M': None, 'tom1H': None,
                          'tom2L': None, 'tom2M': None, 'tom2H': None,
                          'tom3L': None, 'tom3M': None, 'tom3H': None,
                          'crashL': None, 'crashM': None, 'crashH': None,
                          'rideL': None, 'rideM': None, 'rideH': None,
                          'hhoL': None, 'hhoM': None, 'hhoH': None,
                          'hhcL': None, 'hhcM': None, 'hhcH': None,
                          'footL': None, 'footM': None, 'footH': None }

class MidiProc:
    def __init__(self):
        self.rawm = RawMidi(handle_midievent)

# https://static.roland.com/assets/media/pdf/HD-1_r_e2.pdf

def handle_midievent(status, note, velocity):
    low = 62
    high = 94
    # filter note-on messages
    if 144 <= status <= 159:
        # filter kick drum
        if note == 36:
            midinote2sample('kick', velocity, low, high)
        # filter snare drum
        elif note == 38:
            midinote2sample('snare', velocity, low, high)
        # filter tom hi
        elif note == 48:
            midinote2sample('tom1', velocity, low, high)
        # filter tom mid
        elif note == 45:
            midinote2sample('tom2', velocity, low, high)
        # filter tom low
        elif note == 43:
            midinote2sample('tom3', velocity, low, high)
        # filter crash
        elif note == 49:
            midinote2sample('crash', velocity, low, high)
        # filter ride
        elif note == 51:
            midinote2sample('ride', velocity, low, high)
        # filter hh open
        elif note == 46:
            midinote2sample('hho', velocity, low, high)
        # filter hh close
        elif note == 42:
            midinote2sample('hhc', velocity, low, high)
        # filter foot closed
        elif note == 44:
            midinote2sample('foot', velocity, low, high)
    #filter program change
    elif 192 <= status <= 207:
        sampleplayer.set_kit('DK%s' % note)
    #filter control change
    #elif 176 <= status <= 191 and note == 4:

def midinote2sample(pad, velocity, low, high):
    if velocity <= low:
        sampleplayer.execute('%sL' % pad)
    elif velocity >= high:
        sampleplayer.execute('%sH' % pad)
    else:
        sampleplayer.execute('%sM' % pad)


class Modulator:
    def __init__(self):
        # Effect Chain:
        # Input -> 'Compressor' - >'Distortion'
        # -> 'Frequency Shifter' -> 'Chorus' -> 'Reverb'
        # -> 'Volume' -> Speaker

        # Effect parameters:
        # 'Volume-param': between 0 and 1
        # 'Compressor-param': between 0 and 10
        # 'Distortion-param': between 0 and 1
        # 'FreqShift-param': amount of shifting in Hertz
        # 'Chorus-param': between 0 and 5
        # 'Reverb-param': between 0 and 1

        self.effectchain = {'Volume': False, 'Volume-param': 1.0,
                            'Compressor': False, 'Compressor-param': 0.1,
                            'Distortion': False, 'Distortion-param': 0,
                            'FreqShift': False, 'FreqShift-param': 0,
                            'Chorus': False, 'Chorus-param': 0,
                            'Reverb': False, 'Reverb-param': 0}

    def execute(self, player):
        denorm_noise = Noise(1e-24)
        if self.effectchain['Compressor']:
            compressor = Compress(player,
                                  ratio=self.effectchain['Compressor-param'],
                                  thresh=-36,
                                  falltime=0.18)
        else:
            compressor = player
        if self.effectchain['Distortion']:
            distortion = Disto(compressor,
                               drive=self.effectchain['Distortion-param'],
                               slope=0.7)
        else:
            distortion = compressor
        if self.effectchain['FreqShift']:
            freqshift = FreqShift(distortion + denorm_noise,
                                  self.effectchain['FreqShift-param'])
        else:
            freqshift = distortion + denorm_noise
        if self.effectchain['Chorus']:
            chorus = Chorus(freqshift,
                            depth=self.effectchain['Chorus-param'],
                            feedback=random.random(),
                            bal=0.6)
        else:
            chorus = freqshift
        if self.effectchain['Reverb']:
            self.output = Freeverb(chorus,
                                   size=self.effectchain['Reverb-param'],
                                   damp=0.6 + random.random(),
                                   bal=0.7)
        else:
            self.output = chorus
        if self.effectchain['Volume']:
            self.output.setMul(self.effectchain['Volume-param'])
        else:
            self.output.setMul(1)
        self.output = self.output.mix(2)
        self.output.out()

    def toggle_effect(self, name, state):
        if name in self.effectchain:
            self.effectchain[name] = state

    def set_effect_param(self, param, value):
        if param in self.effectchain:
            self.effectchain[param] = value


class NetConHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        command = self.request[0].strip()
        print(command)
        # todo: choose command format (maybe JSON?)
        #       and implement commands.
        #       some ugly examples:
        if command.startswith("dk"): # extra drumkit selector for midi input
            sampleplayer.set_kit(command.split(':')[1])
        elif command.startswith("ec"): # effect chain turn on & off
            modulator.toggle_effect(command.split(':')[1])
        elif command.startswith("ds"): # drum input select -- midi or line in            
            drumselector() # todo
        elif command == 'test': # test system with sample sound
            test() #todo
        elif command == 'exit':
            sys.exit(0)
            # and shutdown pi?


class ConnectionManager():
    def __init__(self, host="localhost", port=9998):
        self.port = port
        self.host = host
        self.server = SocketServer.UDPServer((self.host, self.port),
                                             NetConHandler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HANS Drum Brain Server')
    parser.add_argument('-m', '--midi',
                        help='Input MIDI channel number',
                        default=None,
                        type=int)
    parser.add_argument('-s', '--sampleroot',
                        help='Samples root folder',
                        default='.')
    args = parser.parse_args()

    if not os.path.isdir(args.sampleroot):
        print("Invalid sample root!")
        sys.exit(64)

    if int(''.join(map(str, getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")

    if sys.platform.startswith("win"):
        server = Server()
    else:
        server = Server(audio='jack', jackname='HANSDRUM')

    if args.midi:
        server.setMidiInputDevice(args.midi)
    else:
        pm_list_devices()
        inid = -1
        while (inid > pm_count_devices()-1 and inid != 99) or inid < 0:
            inid = input("Please select input ID [99 for all]: ")
            server.setMidiInputDevice(inid)
    server.boot()
    server.start()

    modulator = Modulator()
    sampleplayer = SamplePlayer(modulator, sample_root=args.sampleroot)
    midiproc = MidiProc()
    conmanager = ConnectionManager()

    conmanager.server.serve_forever()
