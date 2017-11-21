#!/bin/bash
DIR="$(dirname "${BASH_SOURCE[0]}")"
. ${DIR}/config.sh

python2 ${DRUM_SERVER_DIR}/drum-server.py -m ${DRUM_MIDI_DEV_ID} --ip ${HANS_SERVER_IP} --port ${HANS_SERVER_PORT} -s ${DRUM_SAMPLE_ROOT} -o
