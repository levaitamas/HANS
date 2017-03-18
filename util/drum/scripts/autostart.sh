#!/bin/bash

cd /home/alarm
scripts/Playback_to_Lineout.sh
scripts/Record_from_lineIn_Micbias.sh
sleep 2
./start_jack.sh > ./jack_start_log
./start_netmidi.sh >> ./jack_start_log
sleep 1
cd /home/alarm/HANS/util/drum/web/
python2 /home/alarm/HANS/util/drum/web/drum-web.py -t
