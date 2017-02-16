#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL - WEB

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
"""
from flask import Flask, request, render_template
import argparse
import random
import socket
import cgi

app = Flask(__name__)
drum_addr = 'localhost'
drum_port = 9998

# use socket.socket to send data, example:
def sndStr(msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (drum_addr, drum_port))

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        data = request.form
        if data is None:
            print("Error")
        else:
            msg = data['id']
            if(data['value'] != "undefined"):
                msg += ":" + data['value']
            print(msg)
            sndStr(msg)
    return render_template('drumweb.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HANS DRUM Web')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=8000)
