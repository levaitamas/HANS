#!/bin/bash

kill -9 $(pidof a2jmidid)
kill -9 $(pidof aseqnet)

sleep 1

a2jmidid -e &
aseqnet -p 9999 &

aconnect 20 129
