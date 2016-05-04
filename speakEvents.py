#!/usr/bin/env python
#-*- coding:utf-8 -*-
import grovepi
from pyicloud import PyiCloudService        # pip install pyicloud
from ConfigParser import SafeConfigParser
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
import atexit

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

# Set GrovePi+ ports.
encoder2 = 2  # encoder. if you use, update firmware to v1.2.6.
encoder3 = 3  # encoder. if you use, update firmware to v1.2.6.
icloudbtn = 4  # button iCloud
afn360btn = 5  # button AFN
rgbLED = 7  # RGB LED. if you use, update firmware to v1.2.6
feedLED = 8  # LED
numLEDs = 1 # Num of chain LED

grovepi.pinMode(icloudbtn, 'INPUT')
grovepi.pinMode(afn360btn, 'INPUT')
grovepi.pinMode(rgbLED, 'OUTPUT')
grovepi.pinMode(feedLED, 'OUTPUT')

# Init chain of leds
grovepi.chainableRgbLed_init(rgbLED, numLEDs)

# test colors used in grovepi.chainableRgbLed_test()
testColorBlack = 0   # 0b000 #000000
testColorBlue = 1    # 0b001 #0000FF
testColorGreen = 2   # 0b010 #00FF00
testColorCyan = 3    # 0b011 #00FFFF
testColorRed = 4     # 0b100 #FF0000
testColorMagenta = 5 # 0b101 #FF00FF
testColorYellow = 6  # 0b110 #FFFF00
testColorWhite = 7   # 0b111 #FFFFFF

# patterns used in grovepi.chainableRgbLed_pattern()
thisLedOnly = 0
allLedsExceptThis = 1
thisLedAndInwards = 2
thisLedAndOutwards = 3

# Init Grove Encoder
atexit.register(grovepi.encoder_dis)
grovepi.encoder_en()

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

# Kill mplayer
def killMplayer():
    psCmd = subprocess.Popen(['ps', 'ax'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True, shell=False)
    out = psCmd.communicate()[0]
    for line in out.splitlines():
        if 'mplayer' in line and 'AFN' in line:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)
            grovepi.chainableRgbLed_test(rgbLED, numLEDs, testColorBlack)
            time.sleep(.5)


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
            
            # all chain LED turn off
            grovepi.chainableRgbLed_test(rgbLED, numLEDs, testColorBlack)
    
    # Play AFN
    if foundMplayer == 0:
        # LED turn on
        grovepi.chainableRgbLed_test(rgbLED, numLEDs, channel+1)
        
        # If not found mplayer, run mplayer.
        print('=====> start AFN channel: %s.') % AFNchannels[channel]
        cmd = 'nohup mplayer ' + AFNchannels[channel]
        subprocess.Popen(cmd.split(), stdout=open('/dev/null', 'w'), stderr=open(mplayerLog, 'a'), preexec_fn=os.setpgrp)
        
        # change to next channel
        if 0 <= countButton3 <= len(AFNchannels) - 2:
            countButton3 = channel + 1
        else:
            countButton3 = 0
    else:
        # If found mplayer, remove mplayer log file.
        os.remove(mplayerLog)
    
    # Remove lock file.
    os.remove(lockFile)
    
    # feedback LED turn off
    grovepi.digitalWrite(feedLED, 0)
#
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
    
    # blink LED
    grovepi.digitalWrite(feedLED, 0)
    time.sleep(.3)
    grovepi.digitalWrite(feedLED, 1)

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
    
    # feedback LED turn off
    grovepi.digitalWrite(feedLED, 0)

# main
if __name__ == '__main__':
    while True:
        try:
            [new_val,encoder_val] = grovepi.encoderRead()
            if new_val:
#                print(encoder_val)
                time.sleep(3)
                if 1 <= encoder_val <= 4:
                    killMplayer()
                    afn360(0)
                elif 5 <= encoder_val <= 9:
                    killMplayer()
                    afn360(1)
                elif 10 <= encoder_val <= 14:
                    killMplayer()
                    afn360(2)
                elif 15 <= encoder_val <= 19:
                    killMplayer()
                    afn360(3)
                elif 20 <= encoder_val <= 24:
                    killMplayer()
                    afn360(4)

            if grovepi.digitalRead(icloudbtn) == 1:
                print('=====> push D%d') % icloudbtn
                # feedback LED turn on
                grovepi.digitalWrite(feedLED, 1)
                # speakEvents
                if not os.path.exists(lockFile):
                    speakEvents()
                else:
                    print('=====> locking...')

            if grovepi.digitalRead(afn360btn) == 1:
                print('=====> push D%d') % afn360btn
                # feedback LED turn on
                grovepi.digitalWrite(feedLED, 1)
                # play AFN 360
                if not os.path.exists(lockFile):
                    afn360(countButton3)
                else:
                    print('=====> locking...')
            time.sleep(.1)

        except KeyboardInterrupt:
            grovepi.chainableRgbLed_test(rgbLED, numLEDs, testColorBlack)
            grovepi.digitalWrite(feedLED, 0)
            break

        except IOError:
            print('=====> IO Error.')
