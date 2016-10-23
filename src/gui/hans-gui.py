#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
"""
try:
    from pyo import *
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
try:
    import wx
    if str.startswith(wx.version(), '2'):
        wx.SL_VALUE_LABEL = 0
except ImportError:
    raise SystemError("wxPython not found. Please, install it.")
import fnmatch
import os
import sys
import random
import threading
import time


class OSCManager(object):
    def __init__(self, address='/data/hans', port=9900, host='127.0.0.1'):
        self.address = address
        self.port = port
        self.host = host

    # http://ajaxsoundstudio.com/pyodoc/api/classes/opensndctrl.html#oscdatasend
    def send_data(self, type, data):
        a = OscDataSend(type, self.port, self.port, self.host)
        a.send(data)


class HansMainFrame(wx.Frame):
    def __init__(self, osc_manager, parent=None):
        self.oscmanager = osc_manager
        wx.Frame.__init__(self,
                          parent,
                          title='HANS',
                          size=(700, 400))
        self.SetMinSize(wx.Size(700, 400))
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        panelBox = wx.BoxSizer(wx.VERTICAL)
        panelBox.SetMinSize(wx.Size(700, 550))

        self.soloButton = wx.Button(panel, label='HANSSOLO',
                                    size=wx.Size(500, 80))
        self.soloButton.Bind(wx.EVT_BUTTON, self.enterHyperspace)
        panelBox.Add(self.soloButton, flag=wx.EXPAND)
        panelBox.AddSpacer(20)

        self.ampslide = wx.Slider(panel, -1, 80.0, 0.0, 500.0,
                                  size=(150, -1),
                                  name=('ampslider'),
                                  style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.rmsslide = wx.Slider(panel, -1, 70.0, 0.0, 200.0,
                                  size=(150, -1),
                                  name=('rmsslider'),
                                  style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.censlide = wx.Slider(panel, -1, 6000, 0.0, 10000.0,
                                  size=(150, -1),
                                  name=('censlider'),
                                  style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.yinslide = wx.Slider(panel, -1, 400, 0.0, 1000.0,
                                  size=(150, -1),
                                  name=('yinslider'),
                                  style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.Bind(wx.EVT_SLIDER, self.sliderUpdate)

        self.amplab = wx.StaticText(panel, -1, "AMP",
                                    size=(30, -1),
                                    style=0, name=('amplab'))
        self.rmslab = wx.StaticText(panel, -1, "RMS",
                                    size=(30, -1),
                                    style=0, name=('rmslab'))
        self.cenlab = wx.StaticText(panel, -1, "CEN",
                                    size=(30, -1),
                                    style=0, name=('cenlab'))
        self.yinlab = wx.StaticText(panel, -1, "YIN\tYAN",
                                    size=(30, -1),
                                    style=0, name=('yinlab'))

        panelBox.Add(self.amplab, flag=wx.EXPAND)
        panelBox.Add(self.ampslide, flag=wx.EXPAND)
        panelBox.AddSpacer(20)
        panelBox.Add(self.rmslab, flag=wx.EXPAND)
        panelBox.Add(self.rmsslide, flag=wx.EXPAND)
        panelBox.AddSpacer(20)
        panelBox.Add(self.cenlab, flag=wx.EXPAND)
        panelBox.Add(self.censlide, flag=wx.EXPAND)
        panelBox.AddSpacer(20)
        panelBox.Add(self.yinlab, flag=wx.EXPAND)
        panelBox.Add(self.yinslide, flag=wx.EXPAND)
        panelBox.AddSpacer(20)
        panel.SetSizer(panelBox)

    def sliderUpdate(self, event):
        amppos = self.ampslide.GetValue()/100.0
        rmspos = self.rmsslide.GetValue()/100.0
        cenpos = float(self.censlide.GetValue())
        yinpos = float(self.yinslide.GetValue())
        data = ['amp', amppos, 'rms', rmspos,
                'cen', cenpos, 'yin', yinpos]
        self.oscmanager.send_data('sfsfsfsf', data)

    def enterHyperspace(self, e):
        self.oscmanager.send_data('b', 'solo')


if __name__ == "__main__":
    ##
    # PYO
    # RawMidi is supported only since Python-Pyo version 0.7.6
    if int(''.join(map(str, getVersion()))) < 76:
        raise SystemError("Please, update your Python-Pyo install" +
                          "to version 0.7.6 or later.")
    # Setup server
    server = Server().boot()
    # Uncomment following line to enable debug info
    # server.setVerbosity(8)
    server.start()
    ##
    # COMPONENTS
    oscmanager = OSCManager()
    ##
    # GUI
    app = wx.App()
    HansMainFrame(oscmanager)
    app.MainLoop()
