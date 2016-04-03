#!/usr/bin/env python
#-*- coding:utf-8 -*-
from pyicloud import PyiCloudService    # pip install pyicloud
import datetime
import locale
import json
import subprocess
import time
import os
from ConfigParser import SafeConfigParser
from pprint import pprint

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
parser = SafeConfigParser()
parser.read(filename)

userid = parser.get('account', 'user')
assert isinstance(userid, str)
passwd = parser.get('account', 'pass')
assert isinstance(passwd, str)

api = PyiCloudService(userid, passwd)
d = datetime.datetime.today()

def get_iccdata():
    from_dt = datetime.datetime(d.year, d.month, d.day)
    to_dt = datetime.datetime(d.year, d.month, d.day)
    iccEvent = api.calendar.events(from_dt, to_dt)
    return iccEvent

if __name__ == '__main__':
    events = get_iccdata()

    if len(events) == 0:
        # 一日分のイベントが空
        talk = u"本日の予定はありません。以上"
        subprocess.call("atalk.sh -s 120 \"" + talk + "\"", shell=True)
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
                    print eventTime,
                    subprocess.call("atalk.sh -s 130 \"" + eventTime + "\"", shell=True)

                if key == "endDate":
                    if value[4] == 0 and value[5] == 0:
                        eventEndTime = u"に、"
                    else:
                        eventEndTime = str(value[4]) + u"時" + str(value[5]) + u"分まで、"
                    print eventEndTime,
                    subprocess.call("atalk.sh -s 130 \"" + eventEndTime + "\"", shell=True)

                if key == "title":
                    eventTitle = value + u"の予定があります。"
                    print eventTitle
                    subprocess.call("atalk.sh -s 100 \"" + eventTitle + "\"", shell=True)
                    time.sleep(1)
            # End for
        # End for
        # 一日分のループが終了したら
        endTalk = u"忘れ物はありませんか？。以上"
        subprocess.call("atalk.sh -s 120 \"" + endTalk + "\"", shell=True)
    # End if
