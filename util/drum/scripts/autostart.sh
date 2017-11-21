#!/bin/bash

HANS_DRUM_SCRIPTS_DIR="/home/alarm/HANS/util/drum/scripts"
CIRRUS_NG_SCRIPTS_DIR="/home/alarm/scripts"

# config soundcard
${CIRRUS_NG_SCRIPTS_DIR}/Reset_paths.sh
${CIRRUS_NG_SCRIPTS_DIR}/Playback_to_Lineout.sh
${CIRRUS_NG_SCRIPTS_DIR}/Playback_to_Headset.sh
${CIRRUS_NG_SCRIPTS_DIR}/Record_from_Linein.sh

# start jack server
${HANS_DRUM_SCRIPTS_DIR}/start_jack.sh

# start drum web ui
${HANS_DRUM_SCRIPTS_DIR}/start_web.sh
