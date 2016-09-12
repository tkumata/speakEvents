#!/bin/bash
#
echo "Please continue this script after compiling firmware source."
echo "BTW ino can run on environment of Arduino 1.0.x so you should use Arduino IDE 1.6.0 or 1.6.11, if you use Raspbian for Robots jessie."
echo "Are you ready?"
echo "No ctrl+c / Yes return key."
read

function after_burnning() {
    # install python grovepi library
    sudo python /home/pi/Desktop/GrovePi/Software/Python/setup.py install

    echo ""

    # check version
    sudo python /home/pi/Desktop/GrovePi/Software/Python/grove_firmware_version_check.py
}

function public_firmware_burn() {
    WRKDIR="/home/pi/Desktop/GrovePi"
    HEXNAME="grove_pi_v1_2_6.cpp.hex"

    echo ""
    cd $WRKDIR

    BRANCH_TEXT="$(git branch)"

    if echo "$BRANCH_TEXT" | grep "\* firmware_1_2_6"; then
        echo "You select the branch."
    elif echo "$BRANCH_TEXT" | grep "\* master"; then
        echo "You do not select the branch."
        sudo git checkout firmware_1_2_6
    else
        echo "You do not have the branch."
        sudo git fetch origin
        sudo git checkout firmware_1_2_6
    fi

    cd Firmware/Source/v1.2/grove_pi_v1_2_6
    if [ -f "$HEXNAME" ]; then
        echo "OK"
        avrdude -c gpio -p m328p -U flash:w:"$HEXNAME"
    fi

    after_burnning
}

function myself_firmware_burn() {
    WRKDIR="/home/pi/Arduino/temp"
    HEXNAME="grove_pi_v1_2_6.cpp.hex"

    echo ""
    cd $WRKDIR

    #sudo avrdude -c gpio -p m328p -U lfuse:w:0xFF:m
    #sudo avrdude -c gpio -p m328p -U hfuse:w:0xDA:m
    #sudo avrdude -c gpio -p m328p -U efuse:w:0x05:m

    if [ -f "$HEXNAME" ]; then
        # burn
        echo "OK"
        sudo avrdude -c gpio -p m328p -U flash:w:"$HEXNAME"
    fi

    after_burnning
}

echo "Choose a HEX to run:"
echo =======================
echo 1. Public firmware v1.2.6
echo 2. Your building firmware v1.2.6

read -n1 -p "Select and option:" doit
case $doit in
    1) public_firmware_burn
    ;;
    2) myself_firmware_burn
    ;;
    *) echo Exiting
    ;;
esac
