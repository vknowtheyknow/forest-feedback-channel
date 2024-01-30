#!/bin/sh
. /home/pi/ve/bin/activate
cd /home/pi/lora-multi-ch
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
while true; do 
    date
    python -u /home/pi/lora-multi-ch/service_packet.py tx
    sleep 300
done
