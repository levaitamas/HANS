#!/bin/bash

# following line kills the web-server too
# kill -9 $(pidof python2 /home/alarm/HANS/util/drum/server/drum-server.py)

HANS_SERVER_IP=192.168.0.2

python2 /home/alarm/HANS/util/drum/server/drum-server.py -m 3 -o --ip ${HANS_SERVER_IP}-s /home/alarm/HANS/util/drum/server/
