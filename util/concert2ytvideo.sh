#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# HANS CONCERT TO YOUTUBE VIDEO
#
# Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
#
if [[ $1 == -h* ]]
then
    echo "Usage: $0 audio_file visualisation_file output_file"
    exit 0
fi

AUDIO_FILE="$1"
VISUALISATION_FILE="$2"
FILE_NAME="$3"

ffmpeg -i "$AUDIO_FILE" -i "$VISUALISATION_FILE" -shortest -codec:v copy -codec:a aac -strict -2 -b:a 384k -r:a 48000 "$FILE_NAME"
