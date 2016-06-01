#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
"""
try:
    from pyo import *
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
try:
    import wx
except ImportError:
    raise SystemError("wxPython not found. Please, install it.")
import fnmatch
import os
import sys
import random
import threading
import datetime
import pprint


class SeedGen:
    def __init__(self):
        self.output = self.execute()

    def execute(self):
        self.output = random.randint(1, 102334155)


class Sample:
    def __init__(self, path, category=None):
        assert path
        self.path = path
        self.category = category or os.path.basename(os.path.dirname(path))

class SigProc:
    def __init__(self, audioin):
        self.yin = Yin(audioin, tolerance=0.2, winsize=1024, cutoff=20)
        self.cen = Centroid(audioin, 1024)
        self.rms = Follower(audioin, freq=20)
        self.amp = PeakAmp(audioin)
        self.yinlim = 400
        self.cenlim = 6000
        self.rmslim = 0.6
        self.amplim = 1
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
            'Speed': self.limit(self.outputlist[self.get_output("spe")].value, 0.2),
            'Speed-param': random.choice([-1, 1]) * self.denorm(self.outputlist[self.get_output("spe")].value, 0.5, 1.5),
            'Distortion': self.limit(self.outputlist[self.get_output("dis")].value, 0.2),
            'Distortion-param': self.denorm(self.outputlist[self.get_output("dis")].value, 0.4, 1.0),
            'Frequency Shifter': self.limit(self.outputlist[self.get_output("fre")].value, 0.4),
            'FS-param': self.denorm(self.outputlist[self.get_output("fre")].value, -2000.0, 8000.0),
            'Chorus': self.limit(self.outputlist[self.get_output("cho")].value, 0.2),
            'Chorus-param': self.denorm(self.outputlist[self.get_output("cho")].value, 1.0, 5.0),
            'Reverb': self.limit(self.outputlist[self.get_output("rev")].value, 0.1),
            'Reverb-param': self.denorm(self.outputlist[self.get_output("rev")].value, 0.0, 1.0)
        }

        self.output2 = {
            'Human': self.limit(self.outputlist[self.get_output("Human")].value, 0.5),
            'Machine': self.limit(self.outputlist[self.get_output("Machine")].value, 0.5),
            'Music': self.limit(self.outputlist[self.get_output("Music")].value, 0.5),
            'Nature': self.limit(self.outputlist[self.get_output("Nature")].value, 0.5),
            'Beep': self.limit(self.outputlist[self.get_output("Beep")].value, 0.5),
            'Other': self.limit(self.outputlist[self.get_output("Other")].value, 0.5),
        }

    def set_inputs(self):
        self.inputlist = []
        self.inputlist.append(self.Variable("yin", self.norm(self.yin.get(), 0, self.yinlim)))
        self.inputlist.append(self.Variable("cen", self.norm(self.cen.get(), 0, self.cenlim)))
        self.inputlist.append(self.Variable("rms", self.norm(self.rms.get(), 0, self.rmslim)))
        self.inputlist.append(self.Variable("amp", self.norm(self.amp.get(), 0, self.amplim)))
        print datetime.datetime.now()
        print self.inputlist

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
        self.rulelist.append(self.Rule("yin", "fre", 0.80))
        self.rulelist.append(self.Rule("yin", "cho", 0.95))
        self.rulelist.append(self.Rule("yin", "rev", 0.95))

        self.rulelist.append(self.Rule("cen", "vol", 0.90))
        self.rulelist.append(self.Rule("cen", "spe", 0.90))
        self.rulelist.append(self.Rule("cen", "dis", 0.90))
        self.rulelist.append(self.Rule("cen", "fre", 0.60))
        self.rulelist.append(self.Rule("cen", "cho", 0.90))
        self.rulelist.append(self.Rule("cen", "rev", 0.95))

        self.rulelist.append(self.Rule("rms", "vol", 1.00))
        self.rulelist.append(self.Rule("rms", "dis", 0.8))
        self.rulelist.append(self.Rule("rms", "fre", 0.75))
        self.rulelist.append(self.Rule("rms", "cho", 0.8))
        self.rulelist.append(self.Rule("rms", "rev", 0.6))

        self.rulelist.append(self.Rule("amp", "vol", 1.00))
        self.rulelist.append(self.Rule("amp", "spe", 0.95))
        self.rulelist.append(self.Rule("amp", "dis", 0.8))
        self.rulelist.append(self.Rule("amp", "cho", 0.70))
        
        self.rulelist.append(self.Rule("amp", "Human", 0.70))
        self.rulelist.append(self.Rule("yin", "Human", 0.70))
        self.rulelist.append(self.Rule("amp", "Machine", 0.70))
        self.rulelist.append(self.Rule("yin", "Machine", 0.70))
        self.rulelist.append(self.Rule("amp", "Music", 0.70))
        self.rulelist.append(self.Rule("yin", "Music", 0.70))
        self.rulelist.append(self.Rule("amp", "Nature", 0.70))
        self.rulelist.append(self.Rule("yin", "Nature", 0.70))
        self.rulelist.append(self.Rule("amp", "Beep", 0.70))
        self.rulelist.append(self.Rule("yin", "Beep", 0.70))
        self.rulelist.append(self.Rule("amp", "Other", 0.70))
        self.rulelist.append(self.Rule("yin", "Other", 0.70))
        print datetime.datetime.now()
        print self.rulelist

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
        print datetime.datetime.now()
        print self.outputlist

    def get_output(self, name):
        for output in self.outputlist:
            if output.name == name:
                return self.outputlist.index(output)
        return None

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
    def __init__(self, seed_gen, sample_root='.', enable_ai=True):
        assert seed_gen
        self.seedgen = seed_gen
        self.sample_root = sample_root
        self.sample_list = []
        self.num_of_samples = 0
        self.enable_ai = enable_ai
        self.output = ''
        self.execute()

    def execute(self):
        self.seedgen.execute()
        if self.num_of_samples > 0:
            self.output = self.sample_list[(self.seedgen.output %
                                            self.num_of_samples)]

    def set_sample_root(self, path):
        if os.path.isdir(path):
            self.sample_root = path

    def load_samples_from_folder(self, folder):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.aiff'):
                sample_path = os.path.join(root, filename)
                self.sample_list.append(Sample(sample_path))
        self.num_of_samples = len(self.sample_list)

    def remove_samples_from_folder(self, folder):
        self.sample_list = [sample for sample in self.sample_list if
                            os.path.dirname(sample.path) != folder]
        self.num_of_samples = len(self.sample_list)

    def toggle_ai(self, state):
        self.enable_ai = state


class Mediator(object):
    def __init__(self, chooser=None, modulator=None, sigproc=None):
        self.chooser = chooser
        self.modulator = modulator
        self.sigproc = sigproc

    def set_chooser(self, chooser):
        assert chooser
        self.chooser = chooser

    def set_modulator(self, modulator):
        assert modulator
        self.modulator = modulator
    
    def set_sigproc(self, sigproc):
        assert sigproc
        self.sigproc = sigproc


class UIBaseClass(object):
    def __init__(self, mediator):
        self.set_mediator(mediator)

    def set_mediator(self, mediator):
        assert mediator
        self.mediator = mediator


class HansMainFrame(UIBaseClass, wx.Frame):
    def __init__(self, mediator, parent=None):
        UIBaseClass.__init__(self, mediator)
        wx.Frame.__init__(self,
                          parent,
                          title='HANS',
                          size=(600, 300))
        self.SetMinSize(wx.Size(600, 450))
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        leftBox = wx.BoxSizer(wx.VERTICAL)
        leftBox.SetMinSize(wx.Size(350, 100))
        rightBox = wx.BoxSizer(wx.VERTICAL)
        rightBox.SetMinSize(wx.Size(250, 100))

        self.folderDirButton = wx.DirPickerCtrl(panel, path='.')
        self.folderDirButton.Bind(wx.EVT_DIRPICKER_CHANGED,
                                  self.updateSampleRootDir)
        leftBox.Add(self.folderDirButton, flag=wx.EXPAND)

        self.folderList = wx.CheckListBox(panel)
        self.folderList.Bind(wx.EVT_CHECKLISTBOX, self.updateFolders)
        leftBox.Add(self.folderList, 2, flag=wx.EXPAND)

        self.modulatorList = wx.CheckListBox(panel)
        self.modulatorList.Set(['Volume', 'Speed',
                                'Distortion', 'Frequency Shifter',
                                'Chorus', 'Reverb'])
        self.modulatorList.Bind(wx.EVT_CHECKLISTBOX, self.updateModulators)
        rightBox.Add(self.modulatorList, flag=wx.EXPAND)

        self.soloButton = wx.Button(panel, label='HANSSOLO')
        self.soloButton.Bind(wx.EVT_BUTTON, self.enterHyperspace)
        rightBox.Add(self.soloButton, flag=wx.EXPAND)

        self.aiList = wx.CheckListBox(panel)
        self.aiList.Set(['Disable Modulator AI', 'Disable sample Chooser AI'])
        self.aiList.Bind(wx.EVT_CHECKLISTBOX, self.updateAIs)
        rightBox.Add(self.aiList, flag=wx.EXPAND)

        panelBox = wx.BoxSizer(wx.HORIZONTAL)
        panelBox.Add(leftBox, flag=wx.EXPAND)
        panelBox.Add(rightBox, flag=wx.EXPAND)
        panel.SetSizer(panelBox)        
        
        self.ampslide = wx.Slider(panel, -1, 100.0, 0.0, 500.0,            
            size=(150, -1),
            pos=(400,200),
            name=('ampslider'),
            style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.rmsslide = wx.Slider(panel, -1, 70.0, 0.0, 200.0,
            size=(150, -1),
            pos=(400,250),
            name=('rmsslider'),
            style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.censlide = wx.Slider(panel, -1, 6000, 0.0, 10000.0,
            size=(150, -1),
            pos=(400,300),
            name=('censlider'),
            style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.yinslide = wx.Slider(panel, -1, 400, 0.0, 1000.0,
            size=(150, -1),
            pos=(400,350),
            name=('yinslider'),
            style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.Bind(wx.EVT_SLIDER, self.sliderUpdate)

        self.amplab = wx.StaticText(panel, -1, "AMP", 
            pos=(360,200),
            size=(30, -1),
            style=0, name=('amplab'))
        self.rmslab = wx.StaticText(panel, -1, "RMS", 
            pos=(360,250),
            size=(30, -1),
            style=0, name=('rmslab'))
        self.cenlab = wx.StaticText(panel, -1, "CEN", 
            pos=(360,300),
            size=(30, -1),
            style=0, name=('cenlab'))
        self.yinlab = wx.StaticText(panel, -1, "YIN\nYAN", 
            pos=(360,350),
            size=(30, -1),
            style=0, name=('yinlab'))

    def sliderUpdate(self, event):
        amppos = self.ampslide.GetValue()/100.0
        rmspos = self.rmsslide.GetValue()/100.0
        cenpos = self.censlide.GetValue()
        yinpos = self.yinslide.GetValue()
        self.mediator.sigproc.set_imputlims(yinpos, cenpos, rmspos, amppos)

    def updateSampleRootDir(self, e):
        dirs = []
        for root, dirnames, filenames in os.walk(
                self.folderDirButton.GetPath()):
            for dirname in dirnames:
                dirs.append(dirname)
                self.mediator.chooser.set_sample_root(root)
            self.folderList.Set(dirs)

    def enterHyperspace(self, e):
        threading.Thread(target=doTheWookieeBoogie).start()

    def updateFolders(self, e):
        if self.folderList.IsChecked(e.GetInt()):
            folder = os.path.join(self.mediator.chooser.sample_root,
                                  e.GetString())
            self.mediator.chooser.load_samples_from_folder(folder)
            pass
        else:
            folder = os.path.join(self.mediator.chooser.sample_root,
                                  e.GetString())
            self.mediator.chooser.remove_samples_from_folder(folder)

    def updateModulators(self, e):
        if self.modulatorList.IsChecked(e.GetInt()):
            self.mediator.modulator.toggle_effect(e.GetString(), 1)
        else:
            self.mediator.modulator.toggle_effect(e.GetString(), 0)

    def updateAIs(self, e):
        id = e.GetInt()
        if self.aiList.IsChecked(id):
            if id == 0:
                self.mediator.modulator.toggle_ai(False)
            else:
                self.mediator.modulator.toggle_ai(False)
        else:
            if id == 0:
                self.mediator.modulator.toggle_ai(True)
            else:
                self.mediator.modulator.toggle_ai(True)


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
        elif note == 38 or note == 38 and velocity >= 52:
            if random.random() < 0.3:
                modulator.execute()
        # filter accented ride
        elif note == 59 and velocity >= 64:
            if random.random() < 0.1:
                modulator.execute()
        if random.random() < 0.042:
            modulator.execute()


def doTheWookieeBoogie():
    for _ in xrange(random.randint(42, 64)):
        handle_midievent(145, 36, 125)
        time.sleep(0.07 + random.random()/5)


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
            print datetime.datetime.now()
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(self.effectchain)
        self.chooser.execute()
        sample = self.chooser.output
        player = SfPlayer(sample.path, loop=False)
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
            freqshift = FreqShift(distortion,
                                  self.effectchain['FS-param'] or
                                  random.random() * 220)
        else:
            freqshift = distortion
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


if __name__ == "__main__":
    ##
    # PYO
    # RawMidi is supported only since Python-Pyo version 0.7.6
    if int(''.join(map(str, getVersion()))) < 76:
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")
    # Setup server
    if sys.platform.startswith("win"):
        server = Server(duplex=1).boot()
    else:
        server = Server(duplex=1, audio='jack', jackname='HANS').boot()
    # Uncomment following line to enable debug info
    # server.setVerbosity(8)
    # Set MIDI input
    pm_list_devices()
    inid = -1
    while (inid > pm_count_devices()-1 and inid != 99) or inid < 0:
        inid = input("Please select input ID [99 for all]: ")
    server.setMidiInputDevice(inid)
    server.start()
    ##
    # COMPONENTS
    seedgen = SeedGen()
    chooser = Chooser(seedgen)
    midiproc = MidiProc()
    sigproc = SigProc(Input())
    modulator = Modulator(chooser, sigproc)
    mediator = Mediator(chooser, modulator, sigproc)
    ##
    # GUI
    app = wx.App()
    HansMainFrame(mediator)
    app.MainLoop()
