#!/bin/bash
#
echo "Please continue this script after compiling firmware source."
echo "BTW ino can run on environment of Arduino 1.0.x so you should use Arduino IDE 1.6.0 or 1.6.11, if you use Raspbian for Robots jessie."
echo "Cancel ctrl+c / Continue return key."
read

WRKDIR="/home/pi/my-firmware"

echo "Installing Firmware"

cd $WRKDIR/grove_pi_v1_2_6

if [ -f "grove_pi_v1_2_6.ino.standard.hex" -o -f "/home/pi/Arduino/temp/grove_pi_v1_2_6.cpp.hex" ]; then
    sudo avrdude -c gpio -p m328p -U lfuse:w:0xFF:m
    sudo avrdude -c gpio -p m328p -U hfuse:w:0xDA:m
    sudo avrdude -c gpio -p m328p -U efuse:w:0x05:m

    # burn
    sudo avrdude -c gpio -p m328p -U flash:w:grove_pi_v1_2_6.ino.standard.hex
    #sudo avrdude -c gpio -p m328p -U flash:w:/home/pi/Arduino/temp/grove_pi_v1_2_6.cpp.hex

    # install python grovepi library
    sudo python /home/pi/Desktop/GrovePi/Software/Python/setup.py install

    # check version
    sudo python /home/pi/Desktop/GrovePi/Software/Python/grove_firmware_version_check.py
fi
