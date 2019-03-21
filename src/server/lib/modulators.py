"""
Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>

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
import random
import pyo
from .module_base import HansModule


class Modulator(HansModule):
    def __init__(self, main, enable_ai=True):
        self.main = main
        self.enable_ai = enable_ai
        self.chooser = None

        # Effect Chain:
        # 'Volume' -> 'Speed' -> 'Distortion'
        # -> 'Chorus' -> 'Reverb' -> 'Pan'

        # Effect parameters:
        # 'Volume-param': between 0 and 1
        # 'Speed-param': 1 - original; 0-1 slow; 1< - fast
        # 'Distortion-param': between 0 and 1
        # 'Chorus-param': between 0 and 5
        # 'Reverb-param': between 0 and 1

        self.effect_types = ['Volume', 'Speed', 'Distortion',
                             'Chorus', 'Reverb']
        self.pan_positions = [0.02, 0.25, 0.5, 0.75, 0.98]
        self.effectchain = {}
        for e in self.effect_types:
            self.effectchain[e] = False
            self.effectchain['%s-param' % e] = 0

        self.player = pyo.TableRead(pyo.NewTable(0.1), loop=False)
        denorm_noise = pyo.Noise(1e-24)
        self.distortion = pyo.Disto(self.player, slope=0.7)
        self.sw_distortion = pyo.Interp(self.player, self.distortion, interp=0)
        self.chorus = pyo.Chorus(self.sw_distortion + denorm_noise, bal=0.6)
        self.sw_chorus = pyo.Interp(self.sw_distortion, self.chorus, interp=0)
        self.reverb = pyo.Freeverb(self.sw_chorus + denorm_noise, bal=0.7)
        self.sw_reverb = pyo.Interp(self.sw_chorus, self.reverb, interp=0)
        self.output = pyo.Pan(self.sw_reverb, outs=2, spread=0.1)
        self.output.out()

    def init(self):
        self.chooser = self.main.get_module('chooser')

    def execute(self):
        sample = self.chooser.get_output()
        if sample is None:
            return
        self.player.stop()
        self.player.setTable(sample.audio)
        if self.effectchain['Volume']:
            self.player.setMul(self.effectchain['Volume-param'])
        freq = sample.audio_rate * {True: self.effectchain['Speed-param'],
                                    False: 1}[self.effectchain['Speed']]
        self.player.setFreq(freq)
        for effect in ('Distortion', 'Chorus', 'Reverb'):
            sw = getattr(self, 'sw_%s' % effect.lower())
            sw.interp = int(self.effectchain[effect])

        self.output.setPan(random.choice(self.pan_positions))
        self.player.play()

    def set_effects(self, new_setup):
        self.effectchain = new_setup
        self.distortion.setDrive(self.effectchain['Distortion-param'])
        self.chorus.reset()
        self.chorus.setDepth(self.effectchain['Chorus-param'])
        self.reverb.reset()
        self.reverb.setSize(self.effectchain['Reverb-param'])

    def toggle_effect(self, name, state):
        try:
            self.effectchain[name] = state
        except KeyError:
            pass

    def get_effect_types(self):
        return self.effect_types
