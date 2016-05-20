#!/bin/bash
echo "======================"
echo "Burn GrovePi+ firmware"
echo "======================"
echo
echo "Attention!!! This script compile and BURN firmware."
read -n1 -p "Do you execute this? [y/N]: " ans

if [ "$ans" = "y" -o "$ans" = "Y" ]; then
    current_dir=${PWD##*/}
    src_dir="~/work/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6"
    #src_dir="~/Desktop/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6"
    i=6

    if [ "$current_dir" = "firm126" ]; then
        sE_pid=$(ps -e -o pid,cmd | grep -E "speakEvents*" | grep -v grep | awk '{print $1}')
        if [ "$sE_pid" -gt 0 ]; then
            sudo /etc/init.d/speakEventsService.sh stop
        fi

        if [ -d "$src_dir" ]; then
            rm -rf .build
            rm -rf src
            cp -pr "$src_dir" src
        fi

        echo "Building firmware"
        ino list-models
        ino build -m atmega328

        echo "Installing firmware"
        cd .build/atmega328
        avrdude -c gpio -p m328p -U flash:w:firmware.hex
        if [ "$?" -eq 0 ]; then
            echo "Finish"
            while [ "$i" -gt 0 ]; do
                i=$(($i-1))
                echo $i
                sleep 1
            done
            sudo reboot
        fi
    else
        echo
        echo "woring directory is not firm126."
        echo
        exit 1
    fi
else
    echo
    echo "exit"
    echo
    exit 0
fi
