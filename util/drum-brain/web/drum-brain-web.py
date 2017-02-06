#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL - WEB

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
"""
from flask import Flask
import argparse
import random
import socket

app = Flask(__name__)
drum_addr = 'localhost'
drum_port = 9998

# use socket.socket to send data, example:
def clickCount():
    clickCount.clicks += 1
    if(clickCount.clicks == clickCount.limit):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto('solo', (drum_addr, drum_port))
        clickCount.clicks = 0
        if random.random() < 0.8:
            clickCount.limit += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HANS DRUM Web')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=80)
