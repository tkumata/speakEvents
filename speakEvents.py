#!/usr/bin/env python
#-*- coding:utf-8 -*-
import grovepi
from pyicloud import PyiCloudService        # pip install pyicloud
from ConfigParser import SafeConfigParser
#from pprint import pprint
from distutils import spawn
import datetime
import locale
import json
import subprocess, signal
import time
import os, sys
import platform
import requests, re
import shlex

# Global var
homeDir = os.path.expanduser('~')
configFile = homeDir + '/.speakevents'
lockFile = '/tmp/speakEventsLockfile'
mplayerLog = '/tmp/speakEventsMpLogfile'
countButton3 = 0
weatherurl1 = 'http://www.tenki.jp/forecast/3/16/'                      # Weather info for 'Kanto Plain'
weatherurl2 = 'http://www.tenki.jp/forecast/3/16/4410/13112-daily.html' # Pinpoint weather info for 'Setagaya-ku'
userid = ''
passwd = ''

# Init GrovePi+ ports.
button2 = 2
button3 = 3
#button4 = 4
grovepi.pinMode(button2, 'INPUT')
grovepi.pinMode(button3, 'INPUT')
#grovepi.pinMode(button4, 'OUTPUT')

# Check text speaker
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
    psCmd = subprocess.Popen(['ps', 'ax'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True, shell=False)
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
        cmd = 'nohup mplayer ' + AFNchannels[channel] + ''
        subprocess.Popen(cmd.split(), stdout=open('/dev/null', 'w'), stderr=open(mplayerLog, 'a'), preexec_fn=os.setpgrp)
        
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
        
        w1 = parser.get('weatherurls', 'weather1')
        if not w1 == '':
            weatherurl1 = w1
            assert isinstance(weatherurl1, str)
        
        w2 = parser.get('weatherurls', 'weather2')
        if not w2 == '':
            weatherurl2 = w2
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
    htmlTagPattern = re.compile(r'<[^>]*?>')            # remove html tag pattern

    # Get HTML strings
    req = requests.get(url)
    html = req.text
    strPattern = r'<h2 class="sub_title">(.*)</p>'
    matches = re.finditer(strPattern, html)
    
    for match in matches:
        w = htmlTagPattern.sub('', match.groups()[0])
    
    return w

# Get Weather Info 2
def get_weatherinfo2(url):
    info = []
    htmlTagPattern = re.compile(r'<[^>]*?>')                # remove html tag pattern
    
    # Get HTML strings of today's weather
    req = requests.get(url)
    html = req.text
    tmpPattern = ur'今日の天気(.*?)明日の天気'
    match = re.search(tmpPattern, html, re.DOTALL)
    todaysHtml = match.group(1)
    
    # Get high and low temperature.
    tempPattern = ur'<td class="temp"><span class="bold">(.*)</span>℃</td>'
    matches = re.finditer(tempPattern, todaysHtml)
    info.append(u'気温')
    for match in matches:
        tempN = htmlTagPattern.sub('', match.groups()[0])
        info.append(tempN + u'度')
    # In this step info[] has began following,
    # [気温, N度, N度]
    
    # Get chance of rain.
    rainPattern = ur'<td>(.*)</td>'
    matches = re.finditer(rainPattern, todaysHtml)
    info.append(u'降水確率')
    for match in matches:
        rainN = htmlTagPattern.sub('', match.groups()[0])
        if rainN == '---':
            rainN = u'なし'
        info.append(rainN)
    # In this step info[] has began following,
    # [気温, N度, N度, 降水確率, N%, N%, N%, N%]
    
    if len(info) == 8:
        info.insert(1, u'最高気温')
        info.insert(3, u'最低気温')
        info.insert(6, u'0時6時')
        info.insert(8, u'6時12時')
        info.insert(10, u'12時18時')
        info.insert(12, u'18時24時')
        # Finally info[] has began following,
        # [気温, 最高, N度, 最低, N度, 降水確率, 0時6時, N%, 6時12時, N%, 12時18時, N%, 18時24時, N%]
    
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
        cmd = speaker + ' 130 "' + weatherinfo1 + '"'
        subprocess.call(cmd.split(), shell=False)
        time.sleep(1)
    
    # Speak Weather 2
    weatherinfo2 = get_weatherinfo2(weatherurl2)
    if not len(weatherinfo2) == 0:
        for info in weatherinfo2:
            cmd = speaker + ' 100 "' + info + '"'
            subprocess.call(cmd.split(), shell=False)
        time.sleep(1)
    
    # Speak Events
    events = get_iccdata()
    if len(events) == 0:
        # 一日分のイベントが空
        talk = u'本日の予定はありません。以上'
        cmd = speaker + ' 120 "' + talk + '"'
        subprocess.call(cmd.split(), shell=False)
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
                    cmd = speaker + ' 130 "' + eventTime + '"'
                    subprocess.call(cmd.split(), shell=False)
                if key == 'endDate':
                    if value[4] == 0 and value[5] == 0:
                        eventEndTime = u'、'
                    else:
                        eventEndTime = str(value[4]) + u'時' + str(value[5]) + u'分まで'
                    #print eventEndTime,
                    cmd = speaker + ' 130 "' + eventEndTime + '"'
                    subprocess.call(cmd.split(), shell=False)
                if key == 'title':
                    eventTitle = value + u'の予定があります。'
                    #print eventTitle
                    cmd = speaker + ' 100 "' + eventTitle + '"'
                    subprocess.call(cmd.split(), shell=False)
                    time.sleep(1)
        
        # 一日分のループが終了したら
        endTalk = u'忘れ物はありませんか。以上'
        cmd = speaker + ' 100 "' + endTalk + '"'
        subprocess.call(cmd.split(), shell=False)
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
