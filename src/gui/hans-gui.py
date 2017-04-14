#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS GUI

Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

try:
    import wx
    if str.startswith(wx.version(), '2'):
        wx.SL_VALUE_LABEL = 0
except ImportError:
    raise SystemError("wxPython not found. Please, install it.")
import argparse
import socket


class ConnectionManager():
    def __init__(self, host="localhost", port=9999):
        self.port = port
        self.host = host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_data(self, data):
        self.socket.sendto(data, (self.host, self.port))


class HansMainFrame(wx.Frame):
    def __init__(self, con_manager, parent=None):
        self.conmanager = con_manager
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
        data = {'amp': amppos, 'rms': rmspos,
                'cen': cenpos, 'yin': yinpos}
        self.conmanager.send_data(str(data))

    def enterHyperspace(self, e):
        self.conmanager.send_data('solo')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HANS GUI')
    parser.add_argument('-H', '--host',
                        help='HANS server IP adddress or domain name',
                        default='localhost')
    parser.add_argument('-p', '--port',
                        help='HANS server port',
                        default='9999',
                        type=int)
    args = parser.parse_args()
    conmanager = ConnectionManager(args.host, args.port)
    app = wx.App()
    HansMainFrame(conmanager)
    app.MainLoop()
