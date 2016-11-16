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
import socket

app = Flask(__name__)
hans_addr = ''
hans_port = 0


def clickCount():
    clickCount.clicks += 1
    if(clickCount.clicks == 16):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto('solo', (hans_addr, hans_port))
        clickCount.clicks = 0
        logging.info('SOLO sent')

clickCount.clicks = 0


@app.route('/', methods=['POST', 'GET'])
def index():
    msg = request.args.get('reply')
    if msg is None:
        msg = ""
    client = request.remote_addr
    return render_template('index.html', ip=client, reply=msg)


@app.route('/hanssolo', methods=['POST'])
def hanssolo():
    # hs = request.form['hanssolo']
    logging.info('HANSSOLO clicked')
    clickCount()
    msg = "Wait for the magic!"
    return redirect(url_for('index', reply=msg))


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
