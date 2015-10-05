#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamas Levai <levait@tmit.bme.hu>
                        Beregi Richárd <richard.beregi@sztaki.mta.hu>


"""

from collections import deque

from pyo import *

class MidiProc:
    def __init__(self, server):
        self.output = deque([])
        self.rawm = RawMidi(self.midievent)   

    def execute(self):
        pass

    def midievent(status, note, velocity):
        #if status == 153 && note == 36 && velocity >= 63
        print status, note, velocity 