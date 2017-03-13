#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS WEB

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
"""
from flask import Flask, render_template, redirect, url_for, request
import argparse
import logging
import random
import socket

app = Flask(__name__)
hans_addr = ''
hans_port = 0

# use socket.socket to send data
def sndStr(msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (hans_addr, hans_port))

def clickCount():
    clickCount.clicks += 1
    if(clickCount.clicks == clickCount.limit):
        sndStr('solo')
        logging.info('SOLO sent')
        clickCount.clicks = 0
        if random.random() < 0.8:
            clickCount.limit += 1

clickCount.clicks = 0
clickCount.limit = 4


@app.route('/', methods=['POST', 'GET'])
def index():
    client = request.remote_addr
    if request.method == 'POST':
        data = request.form
        if data is None:
            print("Error")
        else:
            msg = data['id']
            if(data['value'] != "undefined"):
                msg += "." + data['value']
            if(msg == "hanssolo"):
                logging.info('HANSSOLO clicked')
                clickCount()
            else:
                sndStr(msg)
    elif request.method == 'GET':
        msg = request.args.get('reply')
        if msg is None:
            msg = "Please press the button above!"
    return render_template('index.html', ip=client, reply=msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HANS Web')
    parser.add_argument('-t', '--testing',
                        help='Turn on testing mode',
                        action='store_true')
    args = parser.parse_args()

    logging.basicConfig(filename='hans-web.log',
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %I:%M:%S',
                        level=logging.INFO)
    logging.info('HANS-WEB started')

    if args.testing:
        hans_addr = 'localhost'
        hans_port = 9999
        app.run(host='0.0.0.0')
    else:
        hans_addr = '192.168.0.3'
        hans_port = 9999
        app.run(host='0.0.0.0', port=80)
