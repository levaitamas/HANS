#!/bin/bash
jack_control start
sudo schedtool -R -p 98 `pidof jackdbus`
jack_control eps realtime true
jack_control ds alsa
jack_control dps softmode true
jack_control dps device hw:sndrpiwsp
jack_control dps rate 48000
jack_control dps nperiods 3
jack_control dps period 128
sleep 1