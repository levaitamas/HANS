#!/bin/bash
DIR="$(dirname "${BASH_SOURCE[0]}")"
. ${DIR}/config.sh

kill -9 $(pidof jacktrip)
sleep 1

jacktrip -c ${HANS_SERVER_IP}
