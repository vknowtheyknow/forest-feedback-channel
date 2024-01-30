#!/bin/sh
. /home/pi/ve/bin/activate
cd /home/pi/lora-multi-ch
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
while true; do 
    date
    python -u /home/pi/lora-multi-ch/lora_receiver/merge.py
    python -u /home/pi/lora-multi-ch/lora_receiver/uploader.py
    echo sleep
    sleep 300
done
