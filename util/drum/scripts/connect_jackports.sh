#!/bin/bash

jack_disconnect JackTrip:send_1 system:capture_1
jack_disconnect JackTrip:send_2 system:capture_2
jack_disconnect JackTrip:receive_1 system:playback_1
jack_disconnect JackTrip:receive_2 system:playback_2

jack_connect HANSDRUM:output_1 JackTrip:send_1
jack_connect HANSDRUM:output_2 JackTrip:send_2
