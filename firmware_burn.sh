#!/bin/bash
#
echo "Please run this script after compiling firmware source. BTW ino can run in Arduino 1.0.x so you should use Arduino IDE."
read
WRKDIR="/home/pi/firm126"

echo "Installing Firmware"
cd $WRKDIR/grove_pi_v1_2_6
sudo avrdude -c gpio -p m328p -U lfuse:w:0xFF:m
sudo avrdude -c gpio -p m328p -U hfuse:w:0xDA:m
sudo avrdude -c gpio -p m328p -U efuse:w:0x05:m
sudo avrdude -c gpio -p m328p -U flash:w:grove_pi_v1_2_6.ino.standard.hex
#sudo python /home/pi/Desktop/GrovePi/Software/Python/setup.py install
sudo python /home/pi/Desktop/GrovePi/Software/Python/grove_firmware_version_check.py
