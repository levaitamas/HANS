#!/usr/bin/env python3
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

import argparse
try:
    import wx
    if str.startswith(wx.version(), '2'):
        wx.SL_VALUE_LABEL = 0
except ImportError:
    raise SystemError("wxPython not found. Please, install it.")
try:
    import pythonosc.udp_client
    import pythonosc.osc_bundle_builder
    import pythonosc.osc_message_builder
except ImportError:
    raise SystemError("python-osc not found. Please, install it.")


class ConnectionManager():
    def __init__(self, host="localhost", port=5005):
        self.client = pythonosc.udp_client.UDPClient(host, port)
        self.addresses = {'solo': '/hans/cmd/solo',
                          'samplereload': '/hans/cmd/samplereload',
                          'rulesreload': '/hans/cmd/rulesreload',
                          'kick': '/hans/midi'}
        for param in ['amp', 'rms', 'cen', 'yin']:
            self.addresses[param] = '/hans/ctrl/%s' % param

    def get_url(self, name):
        return self.addresses[name]

    def send_message(self, address, osc_type, data):
        bundle = pythonosc.osc_bundle_builder.OscBundleBuilder(
            pythonosc.osc_bundle_builder.IMMEDIATELY)
        msg = pythonosc.osc_message_builder.OscMessageBuilder(address)
        msg.add_arg(data, osc_type)
        bundle.add_content(msg.build())
        self.client.send(bundle.build())

    def send_message_with_lookup(self, target, osc_type, data):
        self.send_message(self.get_url(target), osc_type, data)


class HansMainFrame(wx.Frame):
    def __init__(self, con_manager, parent=None):
        self.conmanager = con_manager
        size = (700, 500)
        wx.Frame.__init__(self,
                          parent,
                          title='HANS',
                          size=size)
        self.SetMinSize(wx.Size(size))
        self.initUI()
        self.Centre()
        self.Show()

    def initUI(self):
        panel = wx.Panel(self)
        panelBox = wx.BoxSizer(wx.VERTICAL)
        buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        soloButton = wx.Button(panel,
                               name='solobutton',
                               label='HANSSOLO',
                               size=wx.Size(300, 80))
        kickButton = wx.Button(panel,
                               name='kickbutton',
                               label='KICK',
                               size=wx.Size(100, 80))
        samplereloadButton = wx.Button(panel,
                                       name='samplereloadbutton',
                                       label='Reload Samples')
        rulesreloadButton = wx.Button(panel,
                                      name='rulesreloadbutton',
                                      label='Reload Rules')
        slideStyle = wx.SL_HORIZONTAL | wx.SL_VALUE_LABEL
        ampslide = wx.Slider(panel, -1, 80.0, 0.0, 500.0,
                             size=(150, -1), style=slideStyle,
                             name='ampslider')
        rmsslide = wx.Slider(panel, -1, 70.0, 0.0, 200.0,
                             size=(150, -1), style=slideStyle,
                             name='rmsslider')
        censlide = wx.Slider(panel, -1, 6000, 0.0, 10000.0,
                             size=(150, -1), style=slideStyle,
                             name='censlider')
        yinslide = wx.Slider(panel, -1, 400, 0.0, 1000.0,
                             size=(150, -1), style=slideStyle,
                             name='yinslider')
        amplab = wx.StaticText(panel, -1, "AMP (peak amplitude)",
                               size=(30, -1), style=0)
        rmslab = wx.StaticText(panel, -1, "RMS (root-mean-square)",
                               size=(30, -1), style=0)
        cenlab = wx.StaticText(panel, -1, "CEN (spectral centroid)",
                               size=(30, -1), style=0)
        yinlab = wx.StaticText(panel, -1, "YIN (frequency)",
                               size=(30, -1), style=0)

        buttonBox.AddSpacer(20)
        for name, space in [('solo', 10),
                            ('kick', 40),
                            ('samplereload', 10),
                            ('rulesreload', 20)]:
            attr = '%sButton' % name
            buttonBox.Add(locals()[attr], flag=wx.EXPAND)
            buttonBox.AddSpacer(space)

        panelBox.AddSpacer(20)
        panelBox.Add(buttonBox)
        panelBox.AddSpacer(20)
        for name in ['amp', 'rms', 'cen', 'yin']:
            for type in ['lab', 'slide']:
                attr = '%s%s' % (name, type)
                panelBox.Add(locals()[attr], flag=wx.EXPAND)
            panelBox.AddSpacer(20)

        panel.SetSizer(panelBox)

        self.Bind(wx.EVT_SLIDER, self.sliderUpdate)
        self.Bind(wx.EVT_BUTTON, self.buttonPush)

    def sliderUpdate(self, event):
        name = event.GetEventObject().GetName().replace('slider', '')
        value = float(event.GetEventObject().GetValue())
        if any(True for n in ['rms', 'amp'] if n in name):
            value = value / 100.0
        self.conmanager.send_message_with_lookup(name, 'f', value)

    def buttonPush(self, event):
        name = event.GetEventObject().GetName().replace('button', '')
        typ, val = 'i', 1
        if 'kick' in name:
            typ, val = 'm', (1, 145, 36, 125)
        self.conmanager.send_message_with_lookup(name, typ, val)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HANS GUI')
    parser.add_argument('-H', '--host',
                        help='HANS server IP adddress or name',
                        default='localhost')
    parser.add_argument('-p', '--port',
                        help='HANS server port',
                        default=5005,
                        type=int)
    args = parser.parse_args()
    conmanager = ConnectionManager(args.host, args.port)
    app = wx.App()
    HansMainFrame(conmanager)
    app.MainLoop()
