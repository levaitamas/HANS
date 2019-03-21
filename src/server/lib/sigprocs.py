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
import re
import threading
import time
from collections import namedtuple

import pyo

from .module_base import HansModule


class SigProc(HansModule):
    Rule = namedtuple('Rule', ['active', 'inactive', 'weight'])
    Analyser = namedtuple('Analyser', ['module', 'limit'])

    def __init__(self, main, audioin, rules_file='hans.rules',
                 update_interval=0.5):
        self.main = main
        self.rules_file = rules_file
        self.audioin = audioin
        self.update_interval = update_interval
        self._terminate = False
        self.modulator = None
        self.analysers = None
        self.inputlist = None
        self.outputlist = None
        self.rulelist = None
        self.toggle_levels = None
        self.output = None

    def init(self):
        self.set_rules_toggle_levels(self.rules_file)
        self.init_analysers(self.audioin)
        self.set_inputlist()
        self.init_outputlist()
        self.modulator = self.main.get_module('modulator')
        threading.Thread(target=self.run).start()

    def init_analysers(self, audioin):
        self.analysers = {'yin': self.Analyser(pyo.Yin(audioin), 400),
                          'cen': self.Analyser(pyo.Centroid(audioin), 6000),
                          'rms': self.Analyser(pyo.Follower(audioin), 0.6),
                          'amp': self.Analyser(pyo.PeakAmp(audioin), 0.8)}

    def run(self):
        while not self._terminate:
            self.execute()
            time.sleep(self.update_interval)
            if self.modulator.enable_ai:
                self.modulator.set_effects(self.output['effects'])

    def terminate(self):
        self._terminate = True
        time.sleep(self.update_interval)

    def execute(self):
        sample_categories = self.main.get_sample_categories()
        self.set_inputlist()
        self.calcout()
        effect_conf = {
            'Volume-param': self.denorm(self.outputlist['Volume'], 0.4, 1.0),
            'Speed-param': self.denorm(self.outputlist['Speed'], 0.4, 1.6),
            'Distortion-param': self.denorm(self.outputlist['Distortion'], 0.4, 1.0),
            'Chorus-param': self.denorm(self.outputlist['Chorus'], 1.0, 4.0),
            'Reverb-param': self.denorm(self.outputlist['Reverb'], 0.0, 0.6),
        }
        effect_conf.update({cat: self.toggle(self.outputlist[cat],
                                             self.toggle_levels[cat])
                            for cat in self.main.get_effect_types()})
        sample_cats = {cat: self.toggle(self.outputlist[cat],
                                        self.toggle_levels[cat])
                       for cat in sample_categories}
        self.output = {'effects': effect_conf, 'samples': sample_cats}

    def set_inputlist(self):
        self.inputlist = {name: self.norm(analyser.module.get(),
                                          0, analyser.limit)
                          for name, analyser in self.analysers.items()}

    def set_inputlim(self, name, value):
        setattr(self, '%slim' % name, value)

    def set_rules_toggle_levels(self, rules_file=None):
        if rules_file:
            self.rules_file = rules_file
        self.rulelist = [self.Rule("%s%s" % (cat, i), cat, 1/i)
                         for cat in self.main.get_effect_types()
                         for i in range(1, 3)]
        self.load_rules(self.rules_file)
        self.toggle_levels = {}
        self.load_toggle_levels(self.rules_file)

    def load_rules(self, rules_file):
        # active | inactive : weight
        regex = r"^\s*(\w+)\s*\|\s*(\w+)\s*\:\s*([-+]?\d*\.\d+|\d)"
        pattern = re.compile(regex)
        with open(rules_file) as rfile:
            for line in rfile:
                caps = re.findall(pattern, line)
                for cap in caps:
                    new_rule = self.Rule(cap[0], cap[1], float(cap[2]))
                    self.rulelist.append(new_rule)

    def load_toggle_levels(self, rules_file):
        # category : weight
        regex = r"^\s*(\w+)\s*\:\s*([-+]?\d*\.\d+|\d)"
        pattern = re.compile(regex)
        with open(rules_file) as rfile:
            for line in rfile:
                caps = re.findall(pattern, line)
                for cap in caps:
                    self.toggle_levels[cap[0]] = float(cap[1])

    def init_outputlist(self):
        self.outputlist = {cat: 0
                           for cat in self.main.get_sample_categories()}
        self.outputlist.update({'%s%s' % (c, i): 0
                                for c in self.main.get_effect_types()
                                for i in ('', '1', '2')})

    def calcout(self):
        for output_name in self.outputlist:
            tmplist = []
            for rule in self.rulelist:
                if output_name == rule.inactive:
                    for rlist in (self.inputlist, self.outputlist):
                        tmplist += [(rlist[name], rule.weight)
                                    for name in rlist if name == rule.active]
            if tmplist:
                self.outputlist[output_name] = self.calcavg(tmplist)
                self.age(output_name)

    def age(self, key):
        try:
            self.outputlist["%s2" % key] = 0.5 * self.outputlist["%s1" % key]
            self.outputlist["%s1" % key] = self.outputlist[key]
        except KeyError:
            pass

    @staticmethod
    def norm(variable, min, max):
        if min < variable < max:
            return (variable - min) / (max - min)
        elif variable <= min:
            return 0
        return 1

    @staticmethod
    def denorm(variable, min, max):
        if variable:
            return variable * (max - min) + min
        return 0

    @staticmethod
    def calcavg(tuplelist):
        numerator = sum([l[0] * l[1] for l in tuplelist])
        denominator = sum([l[1] for l in tuplelist])
        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0

    @staticmethod
    def toggle(variable, limit):
        return variable >= limit
