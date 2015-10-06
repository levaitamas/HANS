#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamás Lévai    <levait@tmit.bme.hu>
Copyright (C) 2015-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
"""
from pyo import *
from collections import deque


class MidiProc():
    def __init__(self):
        self.output = deque([])
        self.rawm = RawMidi(midievent)

    def execute(self):
        pass


def midievent(status, note, velocity):
    # if status == 153 && note == 36 && velocity >= 63:
    print status, note, velocity
