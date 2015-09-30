#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamas Levai <levait@tmit.bme.hu>


"""

from collections import deque

import pyo


class Modulator:
    def __init__(self, midiproc, rtsigproc, chooser):
        self.midiproc = midiproc
        self.rtsigproc = rtsigproc
        self.chooser = chooser
        self.output = deque([])

    def execute(self):
        pass
