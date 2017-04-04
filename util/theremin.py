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
    import pyo
except ImportError:
    raise SystemError("Python-Pyo not found. Please, install it.")
import sys


class AudioGen():
    def __init__(self):
        self.n = pyo.Noise(1e-24)
        self.osc = pyo.FastSine(mul=0)
        self.switch = pyo.Switch(self.osc)
        self.delay = pyo.SmoothDelay(self.switch+self.n, delay=0, maxdelay=2)
        self.reverb = pyo.STRev(self.switch+self.n, bal=0)
        self.reverb.out()

    def setOsc(self, osc):
        self.osc = osc
        self.switch.setInput(self.osc)

    def setFreq(self, freq):
        self.osc.setFreq(freq)

    def setAmp(self, amp):
        self.osc.setMul(amp)

    def setDelayTime(self, delay_time):
        self.delay.setDelay(delay_time)

    def setReverbBalance(self, balance):
        self.reverb.setBal(balance)


class ThereminPad(wx.Window):
    def __init__(self, parent, size, audiogen):
        styl = wx.NO_FULL_REPAINT_ON_RESIZE | wx.SUNKEN_BORDER
        super(ThereminPad,
              self).__init__(parent,
                             size=size,
                             style=styl)
        self.audiogen = audiogen
        self.SetBackgroundColour('WHITE')
        self.lines = []
        self.previousPosition = (0, 0)
        self.Bind(wx.EVT_SIZE, self.onSize),
        self.Bind(wx.EVT_IDLE, self.onIdle),
        self.Bind(wx.EVT_PAINT, self.onPaint),
        self.Bind(wx.EVT_MOTION, self.onMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)
        self.initBuffer()

    def initBuffer(self):
        size = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(size.width, size.height)
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.drawLines(dc, *self.lines)
        self.reInitBuffer = False

    def onMotion(self, event):
        if event.Dragging() and event.LeftIsDown():
            freq = event.GetX() * 1.4
            amp = max(1.0 - float(event.GetY())/self.GetSize()[1], 0)
            self.audiogen.setFreq(freq)
            self.audiogen.setAmp(amp)

            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            currentPosition = event.GetPositionTuple()
            lineSegment = self.previousPosition + currentPosition
            self.drawLines(dc, ('Red', [lineSegment]))
            self.currentLine.append(lineSegment)
            self.previousPosition = currentPosition

    def onLeftDown(self, event):
        self.currentLine = []
        self.previousPosition = event.GetPositionTuple()

    def onLeftUp(self, event):
        self.audiogen.setAmp(0)
        self.lines.append(('Red', self.currentLine))
        self.currentLine = []

    def onRightDown(self, event):
        self.audiogen.setAmp(0)

    def onSize(self, event):
        self.reInitBuffer = True

    def onIdle(self, event):
        if self.reInitBuffer:
            self.initBuffer()
            self.Refresh(False)

    def onPaint(self, event):
        wx.BufferedPaintDC(self, self.buffer)

    def clearScreen(self, event):
        self.lines = []
        self.initBuffer()
        self.Refresh()

    @staticmethod
    def drawLines(dc, *lines):
        dc.BeginDrawing()
        for colour, lineSegments in lines:
            pen = wx.Pen(wx.NamedColour(colour), 2, wx.SOLID)
            dc.SetPen(pen)
            for lineSegment in lineSegments:
                dc.DrawLine(*lineSegment)
        dc.EndDrawing()



class ThereminUI(wx.Frame):
    def __init__(self, parent=None):
        wx.Frame.__init__(self,
                          parent,
                          size=(850, 630),
                          style=(wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX),
                          title='HANS THEREMIN')
        self.audiogen = AudioGen()
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        panelBox = wx.BoxSizer(wx.VERTICAL)
        self.clearText = wx.StaticText(panel, label="Clear Screen")
        panelBox.Add(self.clearText, flag=wx.EXPAND|wx.CENTER)
        self.touchRect = ThereminPad(panel, wx.Size(850, 500), self.audiogen)
        panelBox.Add(self.touchRect, flag=wx.EXPAND|wx.CENTER)
        self.clearText.Bind(wx.EVT_LEFT_UP, self.touchRect.clearScreen)
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
        if obj.GetLabel() == "FastSine":
            self.audiogen.setOsc(pyo.FastSine(mul=0))
        elif obj.GetLabel() == "SuperSaw":
            self.audiogen.setOsc(pyo.SuperSaw(mul=0))
        elif obj.GetLabel() == "Blit":
            self.audiogen.setOsc(pyo.Blit(mul=0))
        elif obj.GetLabel() == "SuperSaw":
            self.audiogen.setOsc(pyo.Phasor(mul=0))
        elif obj.GetLabel() == "RCOsc":
            self.audiogen.setOsc(pyo.RCOsc(mul=0))


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        server = pyo.Server()
    else:
        server = pyo.Server(audio='jack', jackname='HANS THEREMIN',
                            duplex=0, ichnls=0)
    server.boot()
    server.start()
    app = wx.App()
    ThereminUI()
    app.MainLoop()
