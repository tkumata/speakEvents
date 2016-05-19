#!/bin/bash
echo "======================"
echo "Burn GrovePi+ firmware"
echo "======================"
echo

echo "Attention!!! This script compile and BURN firmware."
read -n1 -p "Do you execute this? [y/N]: " ans

if [ "$ans" = "y" -o "$ans" = "Y" ]; then
    current_dir=${PWD##*/}

    if [ "$current_dir" = "firm126" ]; then
        sudo /etc/init.d/speakEventsService.sh stop

        rm -rf .build
        rm -rf src
        cp -pr ~/work/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6 src
        #cp -pr ~/Desktop/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6 src

        echo "Building firmware"
        ino list-models
        ino build -m atmega328

        echo "Installing firmware"
        cd .build/atmega328
        avrdude -c gpio -p m328p -U flash:w:firmware.hex

        echo "Finish"

        i=6
        while [ "$i" -gt 0 ]; do
            i=$(($i-1))
            echo $i
            sleep 1
        done
        sudo reboot
        #sudo /etc/init.d/speakEventsService.sh start
    else
        echo
        echo "woring directory is not firm126."
        exit 1
    fi
else
    echo
    echo "exit"
    exit 0
fi
