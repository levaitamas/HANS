#!/bin/bash

# following line kills the web-server too
# kill -9 $(pidof python2 /home/alarm/HANS/util/drum/server/drum-server.py)

python2 /home/alarm/HANS/util/drum/server/drum-server.py -m 3 -s /home/alarm/HANS/util/drum/server/
