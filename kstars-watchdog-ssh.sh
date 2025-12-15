#!/bin/bash

export DISPLAY=:0
XAUTHORITY=`ls /tmp/xauth_* -tr | tail -n1`
xhost +local:

/usr/bin/python3 kstars-watchdog.py
