#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HANS DRUM UTIL - WEB

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

from flask import Flask, request, render_template
import argparse
import socket
import os

app = Flask(__name__)
drum_addr = 'localhost'
drum_port = 9998

# use socket.socket to send data
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
                msg += "." + data['value']
            if(msg == "StartServer"):
                os.system("screen -d -m -S DRUMSERVER bash /home/alarm/start_drumserver.sh")
            elif(msg == "KillServer"):
                os.system("screen -S DRUMSERVER -X quit")
            elif(msg == "StartJacktrip"):
                os.system("screen -d -m -S JACKTRIP bash /home/alarm/start_jacktrip.sh")
            elif(msg == "ConnectJacktrip"):
                os.system("screen -d -m -S JACKCON bash /home/alarm/connect_jackports.sh")
            elif(msg == "reboot"):
                os.system('sudo reboot')
            elif(msg == "poweroff"):
                os.system('sudo poweroff')
            else:
                sndStr(msg)
    return render_template('drumweb.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HANS DRUM Web')
    parser.add_argument('-t', '--testing',
                        help='Turn on testing mode',
                        action='store_true')
    args = parser.parse_args()

    if args.testing:
        app.run(host='0.0.0.0', port=8000)
    else:
        app.run(host='0.0.0.0', port=80)
