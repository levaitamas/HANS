#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL

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
import logging
import os
import sys
import random
import threading
import time


class Sample:
    def __init__(self, path, category=None):
        assert path
        self.path = path
        self.category = category or os.path.basename(os.path.dirname(path))
        self.audio = SndTable(path)
        self.audio_rate = self.audio.getRate()


class Chooser:
    def __init__(self, modulator, sample_root='.'):
        self.modulator = modulator        
        self.sample_root = sample_root
        self.samples =  { 'kickL': None, 'kickM': None, 'kickH': None,
                          'snareL': None, 'snareM': None, 'snareH': None,
                          'tom1L': None, 'tom1M': None, 'tom1H': None,
                          'tom2L': None, 'tom2M': None, 'tom2H': None,
                          'tom3L': None, 'tom3M': None, 'tom3H': None,
                          'crashL': None, 'crashM': None, 'crashH': None,
                          'rideL': None, 'rideM': None, 'rideH': None,
                          'hhOL': None, 'hhOM': None, 'hhOH': None,
                          'hhCL': None, 'hhCM': None, 'hhCH': None,
                          'footL': None, 'footM': None, 'footH': None }
        self.selected_kit = ''
        self.output = None
        self.set_kit('DK1')

    def execute(self, pad):
        self.modulator.execute(self.samples[pad])
        self.output = self.samples[pad]

    def set_kit(self, category):
        self.selected_kit = category
        self.load_samples(os.path.join(self.sample_root, category))

    def load_samples(self, folder):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.wav'):
                path = os.path.join(root, filename)
                self.samples[os.path.basename(filename)] = Sample(path)


class MidiProc:
    def __init__(self):
        self.rawm = RawMidi(handle_midievent)

# https://static.roland.com/assets/media/pdf/HD-1_r_e2.pdf

def handle_midievent(status, note, velocity):
    low = 52
    high = 100
    # filter note-on messages
    if 144 <= status <= 159:
        # filter kick drum
        if note == 36:
            midinote2sample('kick', low, high)
        # filter snare drum
        elif note == 38:
            midinote2sample('snare', low, high)
        # filter tom hi
        elif note == 48:
            midinote2sample('tom1', low, high)
        # filter tom mid
        elif note == 45:
            midinote2sample('tom2', low, high)
        # filter tom low
        elif note == 43:
            midinote2sample('tom3', low, high)
        # filter crash
        elif note == 49:
            midinote2sample('crash', low, high)
        # filter ride
        elif note == 51:
            midinote2sample('ride', low, high) 
        # filter hh open
        elif note == 46:
            midinote2sample('hhO', low, high) 
        # filter hh close
        elif note == 42:
            midinote2sample('hhC', low, high)
        # filter foot closed
        elif note == 44:
            midinote2sample('foot', low, high)
    #filter program change
    elif 192 <= status <= 207:
        chooser.set_kit('DK%s' % note)
    #filter control change
    #elif 176 <= status <= 191 and note == 4:        

def midinote2sample(pad, low, high):
    if velocity <= low:
        chooser.execute('%sL' % pad)
    elif velocity >= high:
        chooser.execute('%sH' % pad)            
    else:
        chooser.execute('%sM' % pad)


class Modulator:
    def __init__(self):
        # Effect Chain:
        # 'Volume' -> 'Speed' -> 'Distortion'
        # -> 'Frequency Shifter' -> 'Chorus' -> 'Reverb'

        # Effect parameters:
        # 'Volume-param': between 0 and 1
        # 'Speed-param': 1 - original; 0-1 slow; 1< - fast
        # 'Distortion-param': between 0 and 1
        # 'FreqShift-param': amount of shifting in Hertz
        # 'Chorus-param': between 0 and 5
        # 'Reverb-param': between 0 and 1

        self.effectchain = {'Volume': False, 'Volume-param': 0,
                            'Speed': False, 'Speed-param': 0,
                            'Distortion': False, 'Distortion-param': 0,
                            'FreqShift': False, 'FreqShift-param': 0,
                            'Chorus': False, 'Chorus-param': 0,
                            'Reverb': False, 'Reverb-param': 0}

    def execute(self, sample):
        player = TableRead(table=sample.audio,
                           freq=sample.audio_rate,
                           loop=False).play()
        denorm_noise = Noise(1e-24)
        if self.effectchain['Volume']:
            player.setMul(self.effectchain['Volume-param'])
        if self.effectchain['Speed']:
            player.setFreq(self.effectchain['Speed-param'])
        if self.effectchain['Distortion']:
            distortion = Disto(player,
                               drive=self.effectchain['Distortion-param'],
                               slope=0.7)
        else:
            distortion = player
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
                                   damp=random.random(), 
                                   bal=0.7)
        else:
            self.output = chorus
        self.output.out()

    def toggle_effect(self, name, state):
        if name in self.effectchain:          
            self.effectchain[name] = state

    def set_effect_param(self, param, value):
        if param in self.effectchain:          
            self.effectchain[param] = value


class HansDrumFrame(wx.Frame):
    def __init__(self, chooser, modulator, parent=None):
        wx.Frame.__init__(self,
                          parent,
                          title='HANS DRUM')
        self.chooser = chooser
        self.modulator = modulator
        self.SetMinSize(wx.Size(1150, 500))
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        panelBox1 = wx.BoxSizer(wx.HORIZONTAL)
        panelBox1.SetMinSize(wx.Size(700, 100))

        self.prevButton = wx.Button(panel, label='PREV',
                                    size=wx.Size(100, 80))
        self.prevButton.Bind(wx.EVT_BUTTON, self.buttonDKChange)
        self.nextButton = wx.Button(panel, label='NEXT',
                                    size=wx.Size(100, 80))
        self.nextButton.Bind(wx.EVT_BUTTON, self.buttonDKChange)
        panelBox1.Add(self.prevButton)
        panelBox1.Add(self.nextButton)
        panelBox1.AddSpacer(20)

        self.volslide = wx.Slider(panel, -1, 100.0, 0.0, 200.0,
                                  size=(80, -1),
                                  name=('Volume-param'),
                                  style=wx.SL_INVERSE| wx.SL_VERTICAL| wx.SL_VALUE_LABEL)
        self.speslide = wx.Slider(panel, -1, 100.0, -200.0, 200.0,
                                  size=(80, -1),
                                  name=('Speed-param'),
                                  style=wx.SL_INVERSE| wx.SL_VERTICAL | wx.SL_VALUE_LABEL)
        self.disslide = wx.Slider(panel, -1, 0.0, 0.0, 100.0,
                                  size=(80, -1),
                                  name=('Distortion-param'),
                                  style=wx.SL_INVERSE| wx.SL_VERTICAL | wx.SL_VALUE_LABEL)
        self.freslide = wx.Slider(panel, -1, 0.0, 0.0, 5000.0,
                                  size=(80, -1),
                                  name=('FreqShift-param'),
                                  style=wx.SL_INVERSE| wx.SL_VERTICAL | wx.SL_VALUE_LABEL)
        self.choslide = wx.Slider(panel, -1, 0.0, 0.0, 500.0,
                                  size=(80, -1),
                                  name=('Chorus-param'),
                                  style=wx.SL_INVERSE| wx.SL_VERTICAL | wx.SL_VALUE_LABEL)
        self.revslide = wx.Slider(panel, -1, 0.0, 0.0, 100.0,
                                  size=(80, -1),
                                  name=('Reverb-param'),
                                  style=wx.SL_INVERSE| wx.SL_VERTICAL | wx.SL_VALUE_LABEL)
        self.Bind(wx.EVT_SLIDER, self.sliderUpdate)

        self.vollab = wx.StaticText(panel, -1, "Volume",
                                    size=(50, -1),
                                    style=0, name=('vollab'))
        self.spelab = wx.StaticText(panel, -1, "Speed",
                                    size=(50, -1),
                                    style=0, name=('spelab'))
        self.dislab = wx.StaticText(panel, -1, "Distortion",
                                    size=(55, -1),
                                    style=0, name=('cenlab'))
        self.frelab = wx.StaticText(panel, -1, "Freq\tShifter",
                                    size=(50, -1),
                                    style=0, name=('frelab'))
        self.cholab = wx.StaticText(panel, -1, "Chorus",
                                    size=(50, -1),
                                    style=0, name=('cholab'))
        self.revlab = wx.StaticText(panel, -1, "Reverb",
                                    size=(50, -1),
                                    style=0, name=('revlab'))
        
        panelBox2 = wx.BoxSizer(wx.HORIZONTAL)
        panelBox2.SetMinSize(wx.Size(700, 300))
        panelBox2.Add(self.vollab, flag=wx.EXPAND)
        panelBox2.Add(self.volslide, flag=wx.EXPAND)
        panelBox2.AddSpacer(10)
        panelBox2.Add(self.spelab, flag=wx.EXPAND)
        panelBox2.Add(self.speslide, flag=wx.EXPAND)
        panelBox2.AddSpacer(10)
        panelBox2.Add(self.dislab, flag=wx.EXPAND)
        panelBox2.Add(self.disslide, flag=wx.EXPAND)
        panelBox2.AddSpacer(20)
        panelBox2.Add(self.frelab, flag=wx.EXPAND)
        panelBox2.Add(self.freslide, flag=wx.EXPAND)
        panelBox2.AddSpacer(20)
        panelBox2.Add(self.cholab, flag=wx.EXPAND)
        panelBox2.Add(self.choslide, flag=wx.EXPAND)
        panelBox2.AddSpacer(20)
        panelBox2.Add(self.revlab, flag=wx.EXPAND)
        panelBox2.Add(self.revslide, flag=wx.EXPAND)
        panelBox2.AddSpacer(20)
        panelBox = wx.BoxSizer(wx.VERTICAL)
        panelBox.Add(panelBox1)
        panelBox.Add(panelBox2)
        panel.SetSizer(panelBox)

    def sliderUpdate(self, event):
        slider = event.GetEventObject()
        self.modulator.effectchain[slider.GetName()] = slider.GetValue() / 100.0

    def buttonDKChange(self, event):
        button = event.GetEventObject()        
        self.chooser.set_kit(button.GetLabel())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HANS Drum Brain')
    parser.add_argument('-m', '--midi',
                        help='Input MIDI channel number',
                        default=None,
                        type=int)
    parser.add_argument('-s', '--sampleroot',
                        help='Path of samples root folder',
                        default='./samples/')
    args = parser.parse_args()

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
    chooser = Chooser(modulator, sample_root=args.sampleroot)
    midiproc = MidiProc()

    app = wx.App()
    HansDrumFrame(chooser, modulator)
    app.MainLoop()