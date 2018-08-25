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
from .module_base import HansModule
from .sample_handling import SampleBank


class ChooserBase(HansModule):
    def __init__(self, main):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError

    def get_output(self):
        self.execute()
        return self.output

    def reload_samples(self):
        self.sample_bank.reload_samples()

    def set_sample_root(self, sample_root):
        self.sample_bank = SampleBank(sample_root)

    def choose_from_categories(self, categories):
        try:
            category = random.choice(categories)
            idx = (self.seedgen.get_output()
                   % len(self.sample_bank.samples[category]))
            self.output = self.sample_bank.samples[category][idx]
        except:
            self.output = None


class BasicChooser(ChooserBase):
    def __init__(self, main):
        self.main = main
        self.output = None

    def init(self):
        self.sample_bank = self.main.get_module('samplebank')
        self.seedgen = self.main.get_module('seedgen')

    def execute(self):
        categories = self.sample_bank.samples.keys()
        self.choose_from_categories(categories)


class IntelligentChooser(ChooserBase):
    def __init__(self, main):
        self.main = main
        self.output = None

    def init(self):
        self.sample_bank = self.main.get_module('samplebank')
        self.sigproc = self.main.get_module('sigproc')
        self.seedgen = self.main.get_module('seedgen')

    def execute(self):
        categories = [c for c, v in
                      self.sigproc.get_output()['samples'].items()
                      if v == True]
        self.choose_from_categories(categories)
