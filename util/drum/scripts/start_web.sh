#!/usr/bin/env bash

DIR="$(dirname "${BASH_SOURCE[0]}")"
. ${DIR}/config.sh

python2 ${DRUM_WEB_DIR}/drum-web.py -t
