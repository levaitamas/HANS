#!/bin/bash

kill -9 $(pidof jacktrip)

sleep 1

jacktrip -c 192.168.0.2
