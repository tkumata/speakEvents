#!/usr/bin/env python
#-*- coding:utf-8 -*-
import grovepi
from pyicloud import PyiCloudService        # pip install pyicloud
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
import requests, re

#homeDir = os.path.expanduser('~')
configFile = '/home/pi/.speakevents'
lockFile = '/tmp/speakEventsLockfile'
mplayerLog = '/tmp/speakEventsMpLogfile'
countButton3 = 0

weatherurl1 = ''
weatherurl2 = ''
userid = ''
passwd = ''

# init Port.
button2 = 2
button3 = 3
#button4 = 4
grovepi.pinMode(button2, 'INPUT')
grovepi.pinMode(button3, 'INPUT')
#grovepi.pinMode(button4, 'OUTPUT')

# check text speaker
if platform.system() == 'Linux':
    if spawn.find_executable('/home/pi/bin/atalk.sh'):
        speaker = '/home/pi/bin/atalk.sh -s'
    else:
        print('=====> atalk.sh がありません。')
        quit()
elif platform.system() == 'Darwin':
    if spawn.find_executable('/usr/bin/say'):
        speaker = '/usr/bin/say -r'
    else:
        print('=====> say がありません。')
        quit()

# AFN channels
AFNchannels = ['http://14023.live.streamtheworld.com/AFNP_TKO',
    'http://14093.live.streamtheworld.com/AFN_JOE',
    'http://4533.live.streamtheworld.com/AFN_PTK',
    'http://6073.live.streamtheworld.com/AFN_VCE',
    'http://14963.live.streamtheworld.com/AFN_FRE'
]

# AFN360 procedure, play and stop
def afn360(channel):
    global countButton3
    
    # create lock file.
    f = open(lockFile, 'w')
    f.close()
    
    # mplayer flag
    foundMplayer = 0
    
    # if this code founds mplayer, kill mplayer and turn on flag.
    psCmd = subprocess.Popen('ps ax', stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True, shell=True)
    out = psCmd.communicate()[0]
    
    # find mplayer process and kill
    for line in out.splitlines():
        if 'mplayer' in line and 'AFN' in line:
            foundMplayer = 1
            print('=====> stop AFN.')
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)
        
    # Play AFN
    if foundMplayer == 0:
        # If not found mplayer, run mplayer.
        print('=====> start AFN channel: %s.') % AFNchannels[channel]
        subprocess.Popen(['nohup', 'mplayer', AFNchannels[channel]],
                         stdout=open('/dev/null', 'w'),
                         stderr=open(mplayerLog, 'a'),
                         preexec_fn=os.setpgrp)
        
        # change to next channel
        if not 0 <= countButton3 <= len(AFNchannels) - 2:
            countButton3 = 0
        else:
            countButton3 = channel + 1
    else:
        # If found mplayer, remove mplayer log file.
        os.remove(mplayerLog)

    # Remove lock file.
    os.remove(lockFile)

# check config file and get iCloud API.
#
# touch ~/.pyicloud && chmod 600 ~/.pyicloud && vi ~/.pyicloud
#[account]
#user = your appleid
#pass = your appleid password
#[weatherurls]
#weather1 = http://www.tenki.jp/forecast/3/16/
#weather2 = http://www.tenki.jp/forecast/3/16/4410/13112-daily.html
#
def get_config():
    global weatherurl1, weatherurl2, userid, passwd
    
    if os.path.isfile(configFile):
        parser = SafeConfigParser()
        parser.read(configFile)

        userid = parser.get('account', 'user')
        assert isinstance(userid, str)

        passwd = parser.get('account', 'pass')
        assert isinstance(passwd, str)

        weatherurl1 = parser.get('weatherurls', 'weather1')
        assert isinstance(weatherurl1, str)

        weatherurl2 = parser.get('weatherurls', 'weather2')
        assert isinstance(weatherurl2, str)
    else:
        print u'=====> config file not found.'
        quit()
    
# get iCloud Calendar data.
def get_iccdata():
    api = PyiCloudService(userid, passwd)

    if not api == '':
        d = datetime.datetime.today()
        from_dt = datetime.datetime(d.year, d.month, d.day)
        to_dt = datetime.datetime(d.year, d.month, d.day)
        
        iccEvents = api.calendar.events(from_dt, to_dt)
        
        return iccEvents
    else:
        print('=====> api is null.')
        quit()
    
# Get Weather Info 1
def get_weatherinfo1(url):
    req = requests.get(url)
    html = req.text

    strPattern = r'<h2 class="sub_title">(.*)</p>'
    tagPattern = re.compile(r'<[^>]*?>')

    matches = re.finditer(strPattern, html)
    
    for match in matches:
        w = tagPattern.sub('', match.groups()[0])

    return w

# Get Weather Info 2
def get_weatherinfo2(url):
    # info : [気温, NN, NN, 降水確率, NN%, NN%, NN%, NN%]
    info = []
    tagPattern = re.compile(r'<[^>]*?>')

    # Weather HTML
    req = requests.get(url)
    html = req.text
    tmpPattern = ur'今日の天気(.*?)明日の天気'
    match = re.search(tmpPattern, html, re.DOTALL)
    todayHtml = match.group(1)
    
    # Get temperature.
    tempPattern = ur'<td class="temp"><span class="bold">(.*)</span>℃</td>'
    matches = re.finditer(tempPattern, todayHtml)
    info.append(u'気温')
    for match in matches:
        tempN = tagPattern.sub('', match.groups()[0])
        info.append(tempN + u'度')
    
    # Get chance of rain.
    rainPattern = ur'<td>(.*)</td>'
    matches = re.finditer(rainPattern, todayHtml)
    info.append(u'降水確率')
    for match in matches:
        rainN = tagPattern.sub('', match.groups()[0])
        if rainN == '---':
            rainN = u'なし'
        info.append(rainN)

    # info : [気温, 最高気温, NN, 最低気温, NN, 降水確率, 0時から6時, NN%, 6時から12時, NN%, 12時から18時, NN%, 18時から24時, NN%]
    if len(info) == 8:
        info.insert(1, u'最高気温')
        info.insert(3, u'最低気温')
        info.insert(6, u'0時から6時')
        info.insert(8, u'6時から12時')
        info.insert(10, u'12時から18時')
        info.insert(12, u'18時から24時')
    else:
        info = []

    return info

# speak events.
def speakEvents():
    # create lock file
    f = open(lockFile, 'w')
    f.close()
    
    # Get config
    get_config()

    # Speak Weather 1
    weatherinfo1 = get_weatherinfo1(weatherurl1)
    if not len(weatherinfo1) == 0:
        subprocess.call(speaker + ' 140 "' + weatherinfo1 + '"', shell=True)
        time.sleep(1)
    
    # Speak Weather 2
    weatherinfo2 = get_weatherinfo2(weatherurl2)
    if not len(weatherinfo2) == 0:
        for info in weatherinfo2:
            subprocess.call(speaker + ' 110 "' + info + '"', shell=True)
        time.sleep(1)
    
    # Speak Events
    events = get_iccdata()
    if len(events) == 0:
        # 一日分のイベントが空
        talk = u'本日の予定はありません。以上'
        subprocess.call(speaker + ' 120 "' + talk + '"', shell=True)
    else:
        events2 = sorted(events, key=lambda x:x['startDate'])    # sort by startDate
        # 一日分のループ
        for event in events2:
            # 個別イベントのループ
            for key,value in event.items():
                if key == 'startDate':
                    if value[4] == 0 and value[5] == 0:
                        eventTime = u'終日'
                    else:
                        eventTime = str(value[4]) + u'時' + str(value[5]) + u'分から'
                    #print eventTime,
                    subprocess.call(speaker + ' 130 "' + eventTime + '"', shell=True)
                if key == 'endDate':
                    if value[4] == 0 and value[5] == 0:
                        eventEndTime = u'に、'
                    else:
                        eventEndTime = str(value[4]) + u'時' + str(value[5]) + u'分まで、'
                    #print eventEndTime,
                    subprocess.call(speaker + ' 130 "' + eventEndTime + '"', shell=True)
                if key == 'title':
                    eventTitle = value + u'の予定があります。'
                    #print eventTitle
                    subprocess.call(speaker + ' 100 "' + eventTitle + '"', shell=True)
                    time.sleep(1)
            # End for
        # End for
        
        # 一日分のループが終了したら
        endTalk = u'忘れ物はありませんか。以上'
        subprocess.call(speaker + ' 120 "' + endTalk + '"', shell=True)
    # End if
    
    # Remove lock file.
    os.remove(lockFile)

#
# main
#
if __name__ == '__main__':
    while True:
        try:
            if grovepi.digitalRead(button2) == 1:
                print('=====> push D2')
                
                if not os.path.exists(lockFile):
                    speakEvents()
                else:
                    print('=====> locking...')
                
            if grovepi.digitalRead(button3) == 1:
                print('=====> push D3')
                
                if not os.path.exists(lockFile):
                    afn360(countButton3)
                else:
                    print('=====> locking...')
                
            time.sleep(.1)
            
        except IOError:
            print('=====> IO Error.')
            quit()
