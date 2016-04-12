#!/usr/bin/env python
#-*- coding:utf-8 -*-
from pyicloud import PyiCloudService    # pip install pyicloud
from ConfigParser import SafeConfigParser
from pprint import pprint
from distutils import spawn
import datetime
import locale
import json
import subprocess, signal
import time
import os, sys
import platform
import daemon
import grovepi

homeDir = os.path.expanduser("~")

# Port init.
button2 = 2
button3 = 3
countButton3 = 0

grovepi.pinMode(button2, "INPUT")
grovepi.pinMode(button3, "INPUT")

# check text speaker
if platform.system() == "Linux":
    if spawn.find_executable('/home/pi/bin/atalk.sh'):
        speaker = "/home/pi/bin/atalk.sh -s"
    else:
        print("atalk.sh がありません。")
        # quit()
elif platform.system() == "Darwin":
    if spawn.find_executable('/usr/bin/say'):
        speaker = "/usr/bin/say -r"
    else:
        print("say がありません。")
        # quit()

# AFN360 procedure
AFNchannels = ['http://13743.live.streamtheworld.com/AFNP_TKO',
    'http://14093.live.streamtheworld.com/AFN_JOE',
    'http://14703.live.streamtheworld.com/AFN_PTK',
    'http://8723.live.streamtheworld.com/AFN_VCE',
    'http://9323.live.streamtheworld.com/AFN_FRE'
]

def afn360(channel):
    global countButton3
    foundMplayer = 0
    ps = subprocess.Popen('ps -A', stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True, shell=True)
    out = ps.communicate()[0]

    # if this founds mplayer, kill mplayer and turn on flag.
    for line in out.splitlines():
        if 'mplayer' in line:
            foundMplayer = 1
            print("stop AFN.")
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)
        else:
            pass

    # play AFN
    if foundMplayer == 0:
        print("start AFN channel: %d.") % channel
        subprocess.Popen(["nohup", "mplayer", AFNchannels[channel]],
                            stdout=open('/dev/null', 'w'), stderr=open('/tmp/speakEventsMplayer.log', 'a'), preexec_fn=os.setpgrp)
        if not 0 <= countButton3 <= len(AFNchannels) - 2:
            countButton3 = 0
        else:
            countButton3 = channel + 1
    else:
        os.remove('/tmp/speakEventsMplayer.log')

# check config file
#
# touch ~/.pyicloud && chmod 600 ~/.pyicloud && vi ~/.pyicloud
#[account]
#user = your appleid
#pass = your appleid password
#
lockFile = "/tmp/speakEventsLockfile"
filename = '/home/pi/.pyicloud'
def get_api():
    if os.path.isfile(filename):
        parser = SafeConfigParser()
        parser.read(filename)

        userid = parser.get('account', 'user')
        assert isinstance(userid, str)

        passwd = parser.get('account', 'pass')
        assert isinstance(passwd, str)

        api = PyiCloudService(userid, passwd)

        return api
    else:
        print u"config file not found."

def get_iccdata():
    api = get_api()

    if not api == "":
        d = datetime.datetime.today()
        from_dt = datetime.datetime(d.year, d.month, d.day)
        to_dt = datetime.datetime(d.year, d.month, d.day)

        iccEvent = api.calendar.events(from_dt, to_dt)

        return iccEvent
    else:
        print("api is null.")
        # quit()

def speakEvents():
    f = open(lockFile, "w")
    f.close()

    events = get_iccdata()

    if len(events) == 0:
        # 一日分のイベントが空
        talk = u"本日の予定はありません。以上"
        subprocess.call(speaker + " 120 \"" + talk + "\"", shell=True)
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
        endTalk = u"忘れ物はありませんか。以上"
        subprocess.call(speaker + " 120 \"" + endTalk + "\"", shell=True)
    # End if
    os.remove(lockFile)

#
# main
#
if __name__ == '__main__':
    while True:
        try:
            if grovepi.digitalRead(button2) == 1:
                print("push D2")

                if not os.path.exists(lockFile):
                    speakEvents()
                else:
                    print("locking...")

            if grovepi.digitalRead(button3) == 1:
                print("push D3")
                afn360(countButton3)

            time.sleep(.3)

        except IOError:
            print("Error")
