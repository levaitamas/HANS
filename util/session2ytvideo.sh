#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# HANS SESSION TO YOUTUBE VIDEO
#
# Copyright (C) 2016-     Tamás Lévai    <levait@tmit.bme.hu>
#
if [[ $1 == -h* ]]
then
    echo "Usage: $0 album_folder_path effect([point|line|p2p|cline]) output_file"
    exit 0
fi

ALBUM_FOLDER="$1"
EFFECT="$2"
FILE_NAME="$3"

cp "$1"/*.flac .
cp "$1"/cover.jpg .

if [ ! -f ./yphil-video-maker.sh ];
then
    wget https://raw.githubusercontent.com/xaccrocheur/kituu/master/scripts/yphil-video-maker.sh
    chmod +x yphil-video-maker.sh
fi

for f in *.flac;
do
    ./yphil-video-maker.sh "$f" HANS `metaflac "$f" --show-tag=TITLE | sed s/.*=//g` cover.jpg "$2"
done

for f in *.mp4;
do
    echo "file '$f'" >> videolist.txt
done

ffmpeg -f concat -safe 0 -i videolist.txt -c copy "$FILE_NAME"

rm videolist.txt
rm yphil-video-maker.sh
