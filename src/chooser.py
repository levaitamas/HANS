#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS

Copyright (C) 2015-     Tamas Levai <levait@tmit.bme.hu>


"""

from collections import deque

import pyo


class Chooser:
    def __init__(self, seed_gen):
        self.seedgen = seed_gen
        self.output = deque([])

    def execute(self):
        pass
