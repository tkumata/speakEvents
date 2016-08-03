#!/bin/bash
echo "======================"
echo "Burn GrovePi+ firmware"
echo "======================"
echo
echo "Attention!!! This script compile and BURN firmware."
read -n1 -p "Do you execute this? [y/N]: " ans

echo
WORK_DIRNAME="firm126"
CURRENT_DIRNAME=${PWD##*/}
#SRC_DIR="~/work/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6"
SRC_DIR="~/Desktop/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6"

if [ "$ans" = "y" -o "$ans" = "Y" ]; then
    i=6

    if [ "$CURRENT_DIRNAME" = "$WORK_DIRNAME" ]; then
        speakEvents_pid=$(ps -e -o pid,cmd | grep -E "speakEvents*" | grep -v grep | awk '{print $1}')
        if [ "${speakEvents_pid:-null}" != null ]; then
            sudo /etc/init.d/speakEventsService.sh stop
        fi

        if [ -d "$SRC_DIR" ]; then
            rm -rf .build
            rm -rf src
            cp -pr "$SRC_DIR" src
        fi

        echo "Building firmware"
        ino list-models
        ino build -m atmega328

        echo "Installing firmware"
        cd .build/atmega328
        avrdude -c gpio -p m328p -U lfuse:w:0xFF:m
        avrdude -c gpio -p m328p -U hfuse:w:0xDA:m
        avrdude -c gpio -p m328p -U efuse:w:0x05:m
        avrdude -c gpio -p m328p -U flash:w:firmware.hex

        if [ "$?" -eq 0 ]; then
            echo "Finished."
            echo "Then reboot after 5 sec."
            while [ "$i" -gt 0 ]; do
                i=$(($i-1))
                echo $i
                sleep 1
            done
            sudo reboot
        fi
    else
        echo
        echo "Woring directory is not $WORK_DIRNAME."
        echo
        exit 1
    fi
else
    echo
    echo "exit"
    echo
    exit 0
fi
