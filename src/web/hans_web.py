#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HANS WEB

Copyright (C) 2016-     Richárd Beregi <richard.beregi@sztaki.mta.hu>
Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>

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

from flask import Flask, render_template, request
from pythonosc import udp_client
import argparse
import logging
import random


app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        data = request.form
        if data:
            msg = data['id']
            if data['value'] != 'undefined':
                msg += "." + data['value']
            if msg == 'hanssolo':
                logging.info('HANSSOLO clicked')
                count_click()

    elif request.method == 'GET':
        warning_text = 'Please press the button above!'
        msg = request.args.get('reply') or warning_text

    return render_template('index.html', ip=request.remote_addr, reply=msg)


def notify_hans(osc_addr, data):
    global osc_client
    osc_client.send_message(osc_addr, data)
    logging.info('OSC message was sent %s to %s' % (data, osc_addr))


def count_click():
    global click_num
    global click_limit
    click_num += 1
    if click_num >= click_limit:
        notify_hans('/hans/cmd/solo', 1)
        click_num = 0
        if random.random() < 0.8:
            click_limit += 1


parser = argparse.ArgumentParser(description='HANS Web')
parser.add_argument('-H', '--host',
                    help='HANS server IP adddress or name',
                    default='localhost')
parser.add_argument('-p', '--port',
                    help='HANS server port',
                    default=5005,
                    type=int)
parser.add_argument('-t', '--testing',
                    help='Turn on testing mode',
                    action='store_true')
parser.add_argument('-v', '--verbose',
                    help='Turn on verbose mode',
                    action='store_true')
parser.add_argument('-l', '--logfile',
                    help='Logfile to store logging info',
                    default='hans-web.log')
args = parser.parse_args()

if args.verbose:
    logging.basicConfig(filename=args.logfile,
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %I:%M:%S',
                        level=logging.INFO)

click_num = 0
click_limit = 4
hans_addr = args.host
hans_port = args.port
osc_client = udp_client.SimpleUDPClient(hans_addr, hans_port)

flask_args = {'host': '0.0.0.0'}
if not args.testing:
    flask_args['port'] = 80

logging.info('HANS-WEB starts')
app.run(**flask_args)
