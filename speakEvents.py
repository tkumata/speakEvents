#!/usr/bin/env python
#-*- coding:utf-8 -*-
from pyicloud import PyiCloudService    # pip install pyicloud
from ConfigParser import SafeConfigParser
from pprint import pprint
from distutils import spawn
import datetime
import locale
import json
import subprocess
import time
import os
import platform
import daemon
import RPi.GPIO as GPIO

# GPIO init.
IO_NO4 = 4
IO_NO5 = 5

GPIO.setmode(GPIO.BCM)

GPIO.setup(IO_NO4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IO_NO5, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# date time
d = datetime.datetime.today()

# check text speaker
if platform.system() == "Linux":
    if spawn.find_executable('/home/pi/bin/atalk.sh'):
        speaker = "/home/pi/bin/atalk.sh -s"
    else:
        print u"text speaker atalk.sh not found."
        quit()
elif platform.system() == "Darwin":
    if spawn.find_executable('/usr/bin/say'):
        speaker = "/usr/bin/say -r"
    else:
        print u"text speaker say not found."
        quit()

# check config file
#
# touch ~/.pyicloud
# chmod 600 ~/.pyicloud
# vi ~/.pyicloud
#[account]
#user = your appleid
#pass = your appleid password
#
homeDir = os.path.expanduser("~")
filename = homeDir + '/.pyicloud'

if os.path.isfile(filename):
    parser = SafeConfigParser()
    parser.read(filename)
    userid = parser.get('account', 'user')
    assert isinstance(userid, str)
    passwd = parser.get('account', 'pass')
    assert isinstance(passwd, str)
    api = PyiCloudService(userid, passwd)
else:
    print u"config file not found."
    quit()

def get_iccdata():
    from_dt = datetime.datetime(d.year, d.month, d.day)
    to_dt = datetime.datetime(d.year, d.month, d.day)
    iccEvent = api.calendar.events(from_dt, to_dt)
    return iccEvent

def speakEvents():
    events = get_iccdata()

    if len(events) == 0:
        # 一日分のイベントが空
        talk = u"本日の予定はありません。以上"
        subprocess.call(speaker + " 120 \"" + talk + "\"", shell=True)
        quit()
    else:
        events2 = sorted(events, key=lambda x:x['startDate'])    # sort by startDate
        # 一日分のループ
        for event in events2:
            # 個別イベントのループ
            for key,value in event.items():
                if key == "startDate":
                    if value[4] == 0 and value[5] == 0:
                        eventTime = u"終日"
                    else:
                        eventTime = str(value[4]) + u"時" + str(value[5]) + u"分から"
                    #print eventTime,
                    subprocess.call(speaker + " 130 \"" + eventTime + "\"", shell=True)

                if key == "endDate":
                    if value[4] == 0 and value[5] == 0:
                        eventEndTime = u"に、"
                    else:
                        eventEndTime = str(value[4]) + u"時" + str(value[5]) + u"分まで、"
                    #print eventEndTime,
                    subprocess.call(speaker + " 130 \"" + eventEndTime + "\"", shell=True)

                if key == "title":
                    eventTitle = value + u"の予定があります。"
                    #print eventTitle
                    subprocess.call(speaker + " 100 \"" + eventTitle + "\"", shell=True)
                    time.sleep(1)
            # End for
        # End for
        # 一日分のループが終了したら
        endTalk = u"忘れ物はありませんか？。以上"
        subprocess.call(speaker + " 120 \"" + endTalk + "\"", shell=True)
    # End if

#
# main
#
if __name__ == '__main__':
    try:
        while True:
            GPIO.wait_for_edge(IO_NO4, GPIO.FALLING)
            print u"4"
            speakEvents()
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit

    try:
        while True:
            GPIO.wait_for_edge(IO_NO5, GPIO.FALLING)
            print u"5"
            #GPIO.outpu(IO_NO5, GPIO.LOW)
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit

    GPIO.cleanup()
