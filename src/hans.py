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


class Chooser:
    def __init__(self, seed_gen, sample_root='.'):
        assert seed_gen
        self.seedgen = seed_gen
        self.sample_root = sample_root
        self.sample_list = []
        self.num_of_samples = 0
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


class Mediator(object):
    def __init__(self, chooser=None, modulator=None):
        self.chooser = chooser
        self.modulator = modulator

    def set_chooser(self, chooser):
        assert chooser
        self.chooser = chooser

    def set_modulator(self, modulator):
        assert modulator
        self.modulator = modulator


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
        self.SetMinSize(wx.Size(600, 300))
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

        panelBox = wx.BoxSizer(wx.HORIZONTAL)
        panelBox.Add(leftBox, flag=wx.EXPAND)
        panelBox.Add(rightBox, flag=wx.EXPAND)
        panel.SetSizer(panelBox)

    def updateSampleRootDir(self, e):
        dirs = []
        for root, dirnames, filenames in os.walk(
                self.folderDirButton.GetPath()):
            for dirname in dirnames:
                dirs.append(dirname)
                self.mediator.chooser.set_sample_root(root)
            self.folderList.Set(dirs)

    def enterHyperspace(self, e):
        doTheWookieeBoogie()

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
            pass

    def updateModulators(self, e):
        if self.modulatorList.IsChecked(e.GetInt()):
            self.mediator.modulator.toggle_effect(e.GetString(), 1)
        else:
            self.mediator.modulator.toggle_effect(e.GetString(), 0)
            pass


class MidiProc:
    def __init__(self):
        self.rawm = RawMidi(handle_midievent)


def handle_midievent(status, note, velocity):
    # filter note-on messages
    if 144 <= status <= 159:
        # filter accented bass drum
        if note == 36 and velocity >= 48:
            if random.random() < 0.6:
                modulator.execute()
        # filter accented snare drum
        elif note == 36 and velocity >= 52:
            if random.random() < 0.3:
                modulator.execute()
        # filter accented ride
        elif note == 59 and velocity >= 64:
            if random.random() < 0.1:
                modulator.execute()


def doTheWookieeBoogie():
    for _ in range(random.randint(42, 64)):
        handle_midievent(145, 36, 125)
        time.sleep(0.07 + random.random()/5)


class Modulator:
    def __init__(self, chooser):
        assert chooser
        self.chooser = chooser
        self.output = None
        # Effect Chain:
        # 'Volume' -> 'Speed' -> 'Distortion'
        # -> 'Frequency Shifter' -> 'Chorus' -> 'Reverb'
        self.effectchain = {'Volume': 0, 'Speed': 0, 'Distortion': 0,
                            'Frequency Shifter': 0, 'Chorus': 0, 'Reverb': 0}

    def execute(self):
        self.chooser.execute()
        sample = self.chooser.output
        player = SfPlayer(sample.path, loop=False)
        if self.effectchain['Volume']:
            player.setMul(random.random())
        if self.effectchain['Speed']:
            player.setSpeed(0.5 + random.random()/2)
        if self.effectchain['Distortion']:
            distortion = Disto(player, drive=random.uniform(0.4, 1),
                               slope=0.7)
        else:
            distortion = player
        if self.effectchain['Frequency Shifter']:
            freqshift = FreqShift(distortion, random.random() * 220)
        else:
            freqshift = distortion
        if self.effectchain['Chorus']:
            chorus = Chorus(freqshift, depth=random.uniform(1, 5),
                            feedback=random.random(), bal=0.6)
        else:
            chorus = freqshift
        if self.effectchain['Reverb']:
            self.output = Freeverb(chorus, size=random.random(),
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


if __name__ == "__main__":
    ##
    # PYO
    # RawMidi is supported only since Python-Pyo version 0.7.6
    if int(''.join(map(str, getVersion()))) < 76:
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")
    # Setup server
    if sys.platform.startswith("win"):
        server = Server().boot()
    else:
        server = Server(audio='jack', jackname='HANS').boot()
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
    modulator = Modulator(chooser)
    mediator = Mediator(chooser, modulator)
    ##
    # GUI
    app = wx.App()
    HansMainFrame(mediator)
    app.MainLoop()
