#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL

Copyright (C) 2016-     Rich�rd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tam�s L�vai    <levait@tmit.bme.hu>
"""
try:
    from pyo import *
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
import argparse
import fnmatch
import os
import sys
import random
import wx
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
            midinote2sample('hhO', velocity, low, high) 
        # filter hh close
        elif note == 42:
            midinote2sample('hhC', velocity, low, high)
        # filter foot closed
        elif note == 44:
            midinote2sample('foot', velocity, low, high)
    #filter program change
    elif 192 <= status <= 207:
        chooser.set_kit('DK%s' % note)
    #filter control change
    #elif 176 <= status <= 191 and note == 4:        

def midinote2sample(pad, velocity, low, high):
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
        self.SetMinSize(wx.Size(650, 500))
        #self.SetDimensions(100, 100, 650, 500)
        self.initUI()
        #self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        font1 = wx.Font(22, wx.MODERN, wx.NORMAL, wx.BOLD)
        font2 = wx.Font(18, wx.MODERN, wx.NORMAL, wx.BOLD)
        font3 = wx.Font(14, wx.TELETYPE, wx.NORMAL, wx.BOLD)
        
        # WX Widget Buttons
        self.dk1Button = wx.Button(panel, label='DK1',
                                    size=wx.Size(50, 100))
        self.dk2Button = wx.Button(panel, label='DK2',
                                    size=wx.Size(50, 100))
        self.dk3Button = wx.Button(panel, label='DK3',
                                    size=wx.Size(50, 100))
        self.dk4Button = wx.Button(panel, label='DK4',
                                    size=wx.Size(50, 100))
        self.dk5Button = wx.Button(panel, label='DK5',
                                    size=wx.Size(50, 100))
        self.dk6Button = wx.Button(panel, label='DK6',
                                    size=wx.Size(50, 100))
        self.dk1Button.SetFont(font1)
        self.dk2Button.SetFont(font1)		
        self.dk3Button.SetFont(font1)		
        self.dk4Button.SetFont(font1)		
        self.dk5Button.SetFont(font1)		
        self.dk6Button.SetFont(font1)
        self.Bind(wx.EVT_BUTTON, self.buttonDKChange)
        
        # WX Widget ToggleButton		
        self.voltb = wx.ToggleButton(panel, -1, 
        	 label='Volume',
        	 name='Volume',
        	 size=(50,100))
        self.spetb = wx.ToggleButton(panel, -1,
        	 label='Speed',
        	 name='Speed',
        	 size=(50,100))
        self.distb = wx.ToggleButton(panel, -1, 
        	 label='Distor\ntion',
        	 name='Distortion',
        	 size=(50,100))
        self.fretb = wx.ToggleButton(panel, -1, 
        	 label='Freq\nShift',
        	 name='FreqShift',
        	 size=(50,100))
        self.chotb = wx.ToggleButton(panel, -1, 
        	 label='Chorus',
        	 name='Chorus',
        	 size=(50,100))
        self.revtb = wx.ToggleButton(panel, -1, 
        	 label='Reverb',
        	 name='Reverb',
        	 size=(50,100))
        self.voltb.SetFont(font2)
        self.spetb.SetFont(font2)
        self.distb.SetFont(font2)
        self.fretb.SetFont(font2)
        self.chotb.SetFont(font2)
        self.revtb.SetFont(font2)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.tbuttonUpdate)
        
        # WX Widget Sliders		 
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
        self.volslide.SetFont(font2)
        self.speslide.SetFont(font2)
        self.disslide.SetFont(font2)
        self.freslide.SetFont(font2)
        self.choslide.SetFont(font2)
        self.revslide.SetFont(font2)
		
        volcol = wx.BoxSizer(wx.HORIZONTAL)
        volcol.AddStretchSpacer(20)
        volcol.Add(self.volslide, flag=wx.EXPAND|wx.CENTER)
        volcol.SetMinSize(wx.Size(80, -1))
        volcol.AddStretchSpacer(20)		
        specol = wx.BoxSizer(wx.HORIZONTAL)
        specol.AddStretchSpacer(20)
        specol.Add(self.speslide, flag=wx.EXPAND|wx.CENTER)
        specol.SetMinSize(wx.Size(80, -1))
        specol.AddStretchSpacer(20)		
        discol = wx.BoxSizer(wx.HORIZONTAL)
        discol.AddStretchSpacer(20)
        discol.Add(self.disslide, flag=wx.EXPAND|wx.CENTER)
        discol.SetMinSize(wx.Size(80, -1))
        discol.AddStretchSpacer(20)		
        frecol = wx.BoxSizer(wx.HORIZONTAL)
        frecol.AddStretchSpacer(20)
        frecol.Add(self.freslide, flag=wx.EXPAND|wx.CENTER)
        frecol.SetMinSize(wx.Size(80, -1))
        frecol.AddStretchSpacer(20)		
        chocol = wx.BoxSizer(wx.HORIZONTAL)
        chocol.AddStretchSpacer(20)
        chocol.Add(self.choslide, flag=wx.EXPAND|wx.CENTER)
        chocol.SetMinSize(wx.Size(80, -1))
        chocol.AddStretchSpacer(20)		
        revcol = wx.BoxSizer(wx.HORIZONTAL)
        revcol.AddStretchSpacer(20)
        revcol.Add(self.revslide, flag=wx.EXPAND|wx.CENTER)
        revcol.SetMinSize(wx.Size(80, -1))
        revcol.AddStretchSpacer(20)
		
        self.Bind(wx.EVT_SLIDER, self.sliderUpdate)

        self.timer = wx.Timer(panel, 1)
        self.timer.Start(1000)
        wx.EVT_TIMER(panel, 1, self.on_timer)
        self.ctime = wx.TextCtrl(panel, -1, time.strftime('%M:%S'), (0, -1), (70, -1), wx.ALIGN_RIGHT)
        self.ctime.Enable(False)
        self.ctime.SetFont(font3)
        timebox = wx.BoxSizer(wx.HORIZONTAL)
        timebox.AddStretchSpacer(8)
        timebox.Add(self.ctime, flag=wx.EXPAND|wx.ALIGN_RIGHT)
        timebox.SetMinSize(wx.Size(20, -1))
        timebox.AddStretchSpacer(2)
        
        panelGrid = wx.FlexGridSizer(rows=4, cols=6, hgap=5, vgap=5)
        # WX Widget Button Row
        panelGrid.Add(self.dk1Button, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.dk2Button, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.dk3Button, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.dk4Button, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.dk5Button, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.dk6Button, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        # WX Widget ToggleButton Row
        panelGrid.Add(self.voltb, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)       
        panelGrid.Add(self.spetb, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.distb, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.fretb, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.chotb, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(self.revtb, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        # WX Widget Slider Row		
        panelGrid.Add(volcol, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(specol, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(discol, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(frecol, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(chocol, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        panelGrid.Add(revcol, 0, flag=wx.ALIGN_CENTER|wx.EXPAND)
        # Clock
        panelGrid.AddSpacer(10)
        panelGrid.AddSpacer(10)
        panelGrid.AddSpacer(10)
        panelGrid.AddSpacer(10)
        panelGrid.AddSpacer(10)
        panelGrid.Add(timebox, 0, wx.ALIGN_CENTER|wx.EXPAND)
        for i in range(6):
            panelGrid.AddGrowableCol(i)
        panelGrid.AddGrowableRow(2)		

        panel.SetSizer(panelGrid)
        panelGrid.Fit(self)
    
    def tbuttonUpdate(self, event):
        tbutton = event.GetEventObject()
        self.modulator.effectchain[tbutton.GetName()] = tbutton.GetValue()
        #print(tbutton.GetName() + " " + str(tbutton.GetValue()))
		
    def sliderUpdate(self, event):
        slider = event.GetEventObject()
        self.modulator.effectchain[slider.GetName()] = slider.GetValue() / 100.0
        #print(slider.GetName() + " " + str(slider.GetValue()/100.0))

    def buttonDKChange(self, event):
        button = event.GetEventObject()        
        self.chooser.set_kit(button.GetLabel())
        #print(button.GetName() + " " + button.GetLabel())

    def on_timer(self, event):
        self.ctime.SetValue(time.strftime('%M:%S'))
        self.ctime.Refresh()
        self.timer.Start(1000)
		

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
