#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS THEREMIN

Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
"""
try:
    import wx
    if str.startswith(wx.version(), '2'):
        wx.SL_VALUE_LABEL = 0
except ImportError:
    raise SystemError("wxPython not found. Please, install it.")
try:
    from pyo import *
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
import sys

class AudioGen():
    def __init__(self):
        self.n = Noise(1e-24)
        self.osc = FastSine(mul=0)
        self.delay = SmoothDelay(self.osc+self.n, delay=0, maxdelay=2)
        self.reverb = STRev(self.delay+self.n, bal=0)
        self.reverb.out()

    def resetChain(self, delay_time, reverb_bal):
        self.delay = SmoothDelay(self.osc+self.n,
                                 delay=delay_time,
                                 maxdelay=2)
        self.reverb = STRev(self.delay+self.n,
                               bal=reverb_bal)
        self.reverb.out()

    def setFreq(self, freq):
        self.osc.setFreq(freq)

    def setAmp(self, amp):
        self.osc.setMul(amp)

    def setDelayTime(self, delay_time):
        self.delay.setDelay(delay_time)

    def setReverbBalance(self, balance):
        self.reverb.setBal(balance)


class ThereminUI(wx.Frame):
    def __init__(self, parent=None):
        wx.Frame.__init__(self,
                          parent,
                          size=(850, 630),
                          title='HANS THEREMIN')
        self.audiogen = AudioGen()
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        panelBox = wx.BoxSizer(wx.VERTICAL)
        self.touchRect = wx.Window(panel,
                              size=wx.Size(700, 500),
                              style=wx.SUNKEN_BORDER)
        self.touchRect.SetBackgroundColour('#FEFEFE')
        self.touchRect.Bind(wx.EVT_MOTION, self.actionOnThereminPad)
        panelBox.Add(self.touchRect, flag=wx.EXPAND|wx.CENTER)
        controlBox = wx.BoxSizer(wx.HORIZONTAL)
        slideBox = wx.BoxSizer(wx.VERTICAL)
        self.delaySlide = wx.Slider(panel, -1, 0.0, 0.0, 200.0,
                                    size=(300, -1),
                                    name=('delayslider'),
                                    style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        self.reverbSlide = wx.Slider(panel, -1, 0.0, 0.0, 100.0,
                                    size=(300, -1),
                                    name=('delayslider'),
                                    style=wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL)
        delayBox = wx.BoxSizer(wx.HORIZONTAL)
        delayBox.Add(wx.StaticText(panel, -1, "Delay", size=(50, 1)))
        delayBox.Add(self.delaySlide)
        slideBox.Add(delayBox, flag=wx.EXPAND)
        reverbBox = wx.BoxSizer(wx.HORIZONTAL)
        reverbBox.Add(wx.StaticText(panel, -1, "Reverb", size=(50, 1)))
        reverbBox.Add(self.reverbSlide)
        slideBox.Add(reverbBox, flag=wx.EXPAND)
        self.Bind(wx.EVT_SLIDER, self.changeEffectParameter)
        oscBox = wx.BoxSizer(wx.HORIZONTAL)
        self.fsineButton = wx.ToggleButton(panel, label='FastSine')
        self.ssawButton = wx.ToggleButton(panel, label='SuperSaw')
        self.blitButton = wx.ToggleButton(panel, label='Blit')
        self.phasorButton = wx.ToggleButton(panel, label='Phasor')
        self.rcoscButton = wx.ToggleButton(panel, label='RCOsc')
        self.fsineButton.SetValue(1)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.switchOsc)
        oscBox.Add(self.fsineButton, flag=wx.EXPAND|wx.CENTER)
        oscBox.Add(self.ssawButton, flag=wx.EXPAND|wx.CENTER)
        oscBox.Add(self.blitButton, flag=wx.EXPAND|wx.CENTER)
        oscBox.Add(self.phasorButton, flag=wx.EXPAND|wx.CENTER)
        oscBox.Add(self.rcoscButton, flag=wx.EXPAND|wx.CENTER)
        controlBox.Add(slideBox, flag=wx.EXPAND|wx.CENTER)
        controlBox.Add(oscBox, flag=wx.EXPAND|wx.CENTER)
        panelBox.Add(controlBox, flag=wx.EXPAND|wx.CENTER)
        panel.SetSizer(panelBox)

    def actionOnThereminPad(self, event):
        if event.LeftIsDown():
            freq = event.GetX() * 1.4
            amp = max(1.0 - float(event.GetY()) / self.touchRect.GetSize()[1],
                      0)
            self.audiogen.setFreq(freq)
            self.audiogen.setAmp(amp)
        elif event.RightIsDown():
            self.audiogen.setAmp(self.audiogen.osc.mul/2)
            self.audiogen.setAmp(0)

    def changeEffectParameter(self, event):
        obj = event.GetEventObject()
        if obj.GetName() == "delayslider":
            self.audiogen.setDelayTime(obj.GetValue() / 100.0)
        if obj.GetName() == "reverbslider":
            self.audiogen.setReverbBalance(obj.GetValue() / 100.0)

    def switchOsc(self, event):
        self.fsineButton.SetValue(0)
        self.ssawButton.SetValue(0)
        self.blitButton.SetValue(0)
        self.phasorButton.SetValue(0)
        self.rcoscButton.SetValue(0)
        obj = event.GetEventObject()
        obj.SetValue(1)
        self.audiogen.reverb.stop()
        delayTime = self.delaySlide.GetValue() / 200.0
        reverbBal = self.reverbSlide.GetValue() / 100.0
        if obj.GetLabel() == "FastSine":
            self.audiogen.osc = FastSine(mul=0)
        elif obj.GetLabel() == "SuperSaw":
            self.audiogen.osc = SuperSaw(mul=0)
        elif obj.GetLabel() == "Blit":
            self.audiogen.osc = Blit(mul=0)
        elif obj.GetLabel() == "SuperSaw":
            self.audiogen.osc = Phasor(mul=0)
        elif obj.GetLabel() == "RCOsc":
            self.audiogen.osc = RCOsc(mul=0)
        self.audiogen.resetChain(delayTime, reverbBal)


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        server = Server()
    else:
        server = Server(audio='jack', jackname='HANS THEREMIN', duplex=0)
    server.boot()
    server.start()
    app = wx.App()
    ThereminUI()
    app.MainLoop()
