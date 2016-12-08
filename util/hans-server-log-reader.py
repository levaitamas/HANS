#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS SERVER LOG READER

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
"""
import json
import os

def load():
	with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'hans-server.log')) as log_data:
		json_data = log_data.read()
		json_data = ("[%s]" % json_data[:-2])
		json_data = json_data.replace("\'", "\"")
		json_data = json_data.replace("True", "true")
		json_data = json_data.replace("False", "false")
		# print(json_data)
        return json.loads(json_data)
		

class Logdata:
    def __init__(self, time, id):
        self.TimeStamp = time
        self.LogId = id

    def setfirstline(self, firstline):
        self.FirstMsg = firstline

    def setsecondline(self, secondline):
        self.SecondMsg = secondline

if __name__ == "__main__":
    data = load()
    print(data)