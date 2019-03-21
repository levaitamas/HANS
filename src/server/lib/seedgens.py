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


class BasicSeedGen(HansModule):
    def __init__(self, main):
        self.output = self.execute()

    def execute(self):
        self.output = int(random.random() * 13579)

    def get_output(self):
        self.execute()
        return self.output


class DummySeedGen(HansModule):
    def __init__(self, main):
        self.main = main
        self.output = 4

    def execute(self):
        pass
