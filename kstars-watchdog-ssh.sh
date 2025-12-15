#!/bin/bash

echo $'\n\n\n\n\n' >> $LOGFILE
date >> $LOGFILE

# Setup X
export DISPLAY=:0
XAUTHORITY=`ls /tmp/xauth_* -tr | tail -n1`
xhost +local:

python kstars-watchdog.py
