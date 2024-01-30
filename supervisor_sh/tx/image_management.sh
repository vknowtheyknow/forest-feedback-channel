#!/bin/sh
. /home/pi/ve/bin/activate
cd /home/pi/lora-multi-ch
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
while true; do
    echo ----------START---------- `date`
    echo ----------camera_controller---------- `date`
    python -u /home/pi/lora-multi-ch/camera_controller
    echo ----------image_classification---------- `date`
    python -u /home/pi/lora-multi-ch/image_classification
    echo ----------STOP---------- `date`
    sleep 900
done
