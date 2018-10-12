#!/usr/bin/env bash

# file structure
DRUM_ROOT=""$(dirname "${BASH_SOURCE[0]}")"/.."
DRUM_SERVER_DIR=${DRUM_ROOT}/server/
DRUM_WEB_DIR=${DRUM_ROOT}/web/
DRUM_SCRIPT_DIR=${DRUM_ROOT}/scripts/
DRUM_SAMPLE_ROOT=${DRUM_SERVER_DIR}

# network
HANS_SERVER_IP=192.168.0.2
HANS_SERVER_PORT=5005

# conections
DRUM_MIDI_DEV_ID=99
