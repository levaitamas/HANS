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
from collections import defaultdict
from pathlib import Path
import pyo

class Sample(object):
    __slots__ = ['path', 'category', 'audio', 'audio_rate']

    def __init__(self, path, category=None):
        self.path = Path(path)
        self.category = category or self.path.parent.name
        self.audio = pyo.SndTable(str(self.path))
        self.audio_rate = self.audio.getRate()

    def __str__(self):
        return "{'Path': '%s', 'Category': '%s'}" \
            % (self.path.name, self.category)


class SampleBank(object):
    def __init__(self, sample_root='.'):
        self.sample_root = sample_root
        self.samples = None
        self.reload_samples()

    def reload_samples(self):
        self.init_samples()
        self.load_samples(self.sample_root)

    def init_samples(self):
        self.samples = defaultdict(list)

    def load_samples(self, sample_root='.'):
        if Path(sample_root).is_dir():
            for sample in Path(sample_root).glob('**/*.aiff'):
                self.samples[sample.parent.name].append(Sample(sample))
        self.check_num_of_samples()

    def check_num_of_samples(self):
        num_of_samples = sum([len(s) for c, s in self.samples.items()])
        if num_of_samples < 1:
            raise Exception("No samples are available!")

    def get_categories(self):
        return self.samples.keys()
