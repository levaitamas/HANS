#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL - SERVER

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
"""
try:
    import pyo
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
import SocketServer
import argparse
import fnmatch
import os
import sys


class Sample:
    def __init__(self, path, category=None):
        assert path
        self.path = path
        self.category = category or os.path.basename(os.path.dirname(path))
        self.audio = pyo.SndTable(path, chnl=1)
        self.audio_rate = self.audio.getRate()
        self.player = pyo.TableRead(table=self.audio,
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
        self.mixer = pyo.Mixer(outs=1, chnls=len(categories))
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
        self.modulator.set_player(self.mixer[0])
        self.modulator.execute()
        self.samples[pad].player.play()

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
        self.rawm = pyo.RawMidi(handle_midievent)

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
        self.input_id = 0;
        # Input IDs
        # 1 - HANSDRUM
        # 0 - External

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

        self.player = pyo.TableRead(pyo.NewTable(1), loop=False)
        self.denorm_noise = pyo.Noise(1e-24)
        self.selector_input = pyo.Selector(
            inputs=[pyo.Input(), self.player])

        self.compressor = pyo.Compress(self.selector_input,
                                       ratio=self.effectchain['Compressor-param'],
                                       thresh=-36,
                                       falltime=0.18)
        self.selector_comp = pyo.Selector(
            inputs=[self.selector_input, self.compressor])

        self.distortion = pyo.Disto(self.selector_comp,
                                    drive=self.effectchain['Distortion-param'],
                                    slope=0.7)
        self.selector_disto = pyo.Selector(
            inputs=[self.selector_comp, self.distortion])

        self.freqshift = pyo.FreqShift(self.selector_disto + self.denorm_noise,
                                       shift=self.effectchain['FreqShift-param'])
        self.selector_freqshift = pyo.Selector(
            inputs=[self.selector_disto, self.freqshift])

        self.chorus = pyo.Chorus(self.selector_freqshift + self.denorm_noise,
                                 depth=self.effectchain['Chorus-param'],
                                 bal=0.6)
        self.selector_chorus = pyo.Selector(
            inputs=[self.selector_freqshift, self.chorus])

        self.reverb = pyo.Freeverb(self.selector_chorus + self.denorm_noise,
                                   size=self.effectchain['Reverb-param'],
                                   bal=0.7)
        self.output = pyo.Selector(inputs=[self.selector_chorus, self.reverb])
        self.output = self.output.mix(2)
        self.output.out()

    def set_player(self, player_out):
        self.player = player_out
        self.selector_input.setInputs([pyo.Input(), self.player])

    def execute(self):
        if self.effectchain['Compressor']:
            self.compressor.setRatio(self.effectchain['Compressor-param']*0.1)
            self.selector_comp.setVoice(1)
        else:
            self.selector_comp.setVoice(0)
        if self.effectchain['Distortion']:
            self.distortion.setDrive(self.effectchain['Distortion-param']*0.01)
            self.selector_disto.setVoice(1)
        else:
            self.selector_disto.setVoice(0)
        if self.effectchain['FreqShift']:
            self.freqshift.setShift(self.effectchain['FreqShift-param']*10)
            self.selector_freqshift.setVoice(1)
        else:
            self.selector_freqshift.setVoice(0)
        if self.effectchain['Chorus']:
            self.chorus.setDepth(self.effectchain['Chorus-param']*0.05)
            self.selector_chorus.setVoice(1)
        else:
            self.selector_chorus.setVoice(0)
        if self.effectchain['Reverb']:
            self.reverb.setSize(self.effectchain['Reverb-param']*0.01)
            self.output.setVoice(1)
        else:
            self.output.setVoice(0)
        if self.effectchain['Volume']:
            self.output.setMul(self.effectchain['Volume-param']*0.011)
        else:
            self.output.setMul(1)

    def toggle_effect(self, name, state):
        if name in self.effectchain:
            self.effectchain[name] = state
            self.execute()

    def set_effect_param(self, param, value):
        if param in self.effectchain:
            self.effectchain[param] = value
            self.execute()

    def set_input(self, value):
        if value == 1:
            self.input_id = 1
            self.selector_input.setVoice(1)
        elif value == 0:
            self.input_id = 1
            self.selector_input.setVoice(1)

    def toggle_input(self):
        if self.input_id:
            self.set_input(0)
        else:
            self.set_input(1)


class NetConHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        command = self.request[0].strip()
        # todo: choose command format (maybe JSON?)
        #       and implement commands.
        #       some ugly examples:
        if command.startswith("DK"): # extra drumkit selector for midi input
            sampleplayer.set_kit(command)
        elif command.startswith("es"): # effect chain switch
            effect_name = command.split('.')[1] 
            if command.split('.')[2] == 'on':
                modulator.toggle_effect(effect_name, True)
            elif command.split('.')[2] == 'off':
                modulator.toggle_effect(effect_name, False)
        elif command.startswith("ec"): # effect chain parameter
            effect_name = command.split('.')[1]
            value = float(command.split('.')[2])
            modulator.set_effect_param(effect_name, value)
        elif command.startswith("ds"): # drum input select -- midi or line in
            modulator.toggle_input()
        elif command == 'test': # test system with sample sound
            test() #todo
        elif command == 'exit':
            # quite destructive. should be confirmed before issuing
            os.system('sudo poweroff')


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
    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose mode',
                        action='store_true')
    args = parser.parse_args()

    if not os.path.isdir(args.sampleroot):
        print("Invalid sample root!")
        sys.exit(64)

    if int(''.join(map(str, pyo.getVersion()))) < 76:
        # RawMidi is supported only since Python-Pyo version 0.7.6
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")

    if sys.platform.startswith("win"):
        server = pyo.Server()
    else:
        server = pyo.Server(duplex=1, audio='jack', jackname='HANSDRUM')

    if args.verbose:
        server.setVerbosity(8)

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

    modulator = Modulator()
    sampleplayer = SamplePlayer(modulator, sample_root=args.sampleroot)
    midiproc = MidiProc()
    conmanager = ConnectionManager()

    conmanager.server.serve_forever()
