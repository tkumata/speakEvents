#!/usr/bin/env python
#-*- coding:utf-8 -*-
import grovepi
from pyicloud import PyiCloudService        # pip install pyicloud
from ConfigParser import SafeConfigParser
from distutils import spawn
import datetime
import locale
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
lockFileB1 = '/tmp/speakEventsLockfileB1'
lockFileB2 = '/tmp/speakEventsLockfileB2'
mplayerLog = '/tmp/speakEventsMpLogfile'
weatherURL1 = 'http://www.tenki.jp/forecast/3/16/'                      # Weather info for 'Kanto Plain'
weatherURL2 = 'http://www.tenki.jp/forecast/3/16/4410/13112-daily.html' # Pinpoint weather info for 'Setagaya-ku'
userid = ''
passwd = ''
radio_on = 0

# Set GrovePi+ ports.
encoder2 = 2    # encoder. if you use it, update firmware to patched v1.2.6. And Encoder work only D2 port.
encoder3 = 3    # encoder. if you use it, update firmware to patched v1.2.6.
icloudBtn = 4   # button iCloud
radioBtn = 5   # button AFN
rgbLED = 7      # RGB LED. if you use it with Encoder, update firmware to patched v1.2.6
feedLED = 8     # LED
numLEDs = 1     # Num of chain LED

grovepi.pinMode(icloudBtn, 'INPUT')
grovepi.pinMode(radioBtn, 'INPUT')
grovepi.pinMode(rgbLED, 'OUTPUT')
grovepi.pinMode(feedLED, 'OUTPUT')

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
else:
    quit()

# Internet Radio channels
radioChannels = ['http://14023.live.streamtheworld.com/AFNP_TKO',
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
    
    if os.path.exists(mplayerLog):
        os.remove(mplayerLog)
    
    # Turn Chainable RGB LED off
    grovepi.chainableRgbLed_test(rgbLED, numLEDs, testColorBlack)

# AFN360 procedure, play and stop
def radio(channel, doPlay):
    # create lock file
    f = open(lockFileB2, 'w')
    f.close()
    
    if doPlay == 1:
        killMplayer()
        
        if channel > 4:
            channel = 1
        
        # Turn Chainable RGB LED on
        grovepi.chainableRgbLed_test(rgbLED, numLEDs, channel+1)
        
        # If not found mplayer, run mplayer.
        print('=====> start AFN channel: %s.') % radioChannels[channel]
        cmd = 'nohup mplayer ' + radioChannels[channel]
        subprocess.Popen(cmd.split(), stdout=open('/dev/null', 'w'), stderr=open(mplayerLog, 'a'), preexec_fn=os.setpgrp)
    
    else:
        killMplayer()
    
    # Remove lock file.
    os.remove(lockFileB2)
    # Turn feedback LED off
    grovepi.digitalWrite(feedLED, 0)

# check config file and get iCloud API.
#
# touch ~/.pyicloud && chmod 600 ~/.pyicloud && vi ~/.pyicloud
#[account]
#user = your appleid
#pass = your appleid password
#[weatherurls]
#weather1 = http://www.tenki.jp/forecast/3/16/
#weather2 = http://www.tenki.jp/forecast/3/16/4410/13112-daily.html
def get_config():
    global weatherURL1, weatherURL2, userid, passwd
    
    if os.path.isfile(configFile):
        parser = SafeConfigParser()
        parser.read(configFile)
        
        userid = parser.get('account', 'user')
        assert isinstance(userid, str)
        
        passwd = parser.get('account', 'pass')
        assert isinstance(passwd, str)
        
        w1 = parser.get('weatherurls', 'weather1')
        if not w1 == '':
            weatherURL1 = w1
            assert isinstance(weatherURL1, str)
        
        w2 = parser.get('weatherurls', 'weather2')
        if not w2 == '':
            weatherURL2 = w2
            assert isinstance(weatherURL2, str)
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
    f = open(lockFileB1, 'w')
    f.close()
    
    # Get config
    get_config()
    
    # Speak Weather 1
    weatherinfo1 = get_weatherinfo1(weatherURL1)
    if not len(weatherinfo1) == 0:
        cmd = speaker + ' 130 "' + weatherinfo1 + '"'
        subprocess.call(cmd.split(), shell=False)
        time.sleep(1)
    
    # Speak Weather 2
    weatherinfo2 = get_weatherinfo2(weatherURL2)
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
    
    # Remove lock file.
    os.remove(lockFileB1)
    
    # Turn feedback LED off
    grovepi.digitalWrite(feedLED, 0)

# main
if __name__ == '__main__':
    # Init LED
    grovepi.digitalWrite(feedLED, 0)
    
    # Init Chainable RGB LED
    grovepi.chainableRgbLed_init(rgbLED, numLEDs)
    
    # Init Grove Encoder
    atexit.register(grovepi.encoder_dis)
    grovepi.encoder_en()
    
    # Init mplayer
    killMplayer()
    
    while True:
        try:
            if radio_on == 1:
                [new_val, encoder_val] = grovepi.encoderRead()
                if new_val:
                    print('=====> Encoder: %d') % encoder_val
                    if not os.path.exists(lockFileB2):
                        radio(encoder_val, radio_on)
            
            if grovepi.digitalRead(icloudBtn) == 1:
                print('=====> Button: D%d') % icloudBtn
                
                # Turn feedback LED on
                grovepi.digitalWrite(feedLED, 1)
                
                # Run speakEvents
                if not os.path.exists(lockFileB1):
                    speakEvents()
                else:
                    print('=====> Locking...')
            
            if grovepi.digitalRead(radioBtn) == 1:
                print('=====> Button: D%d') % radioBtn
                
                # Turn feedback LED on
                grovepi.digitalWrite(feedLED, 1)
                
                # Run internet radio
                if not os.path.exists(lockFileB2):
                    if radio_on == 0:
                        [new_val, encoder_val] = grovepi.encoderRead()
                        print('=====> Encoder: %d') % encoder_val
                        radio_on = 1
                        radio(encoder_val, radio_on)
                    else:
                        radio_on = 0
                        radio(0, radio_on)
                else:
                    print('=====> Locking...')
            
            time.sleep(.1)
        
        except KeyboardInterrupt:
            grovepi.chainableRgbLed_test(rgbLED, numLEDs, testColorBlack)
            grovepi.digitalWrite(feedLED, 0)
            break

        except IOError:
            print('=====> IO Error.')
