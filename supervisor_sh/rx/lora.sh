#!/bin/sh
. /home/pi/ve/bin/activate
cd /home/pi/lora-multi-ch
date
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
python -u /home/pi/lora-multi-ch/lora_receiver