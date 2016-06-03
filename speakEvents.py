#!/usr/bin/env python
#-*- coding:utf-8 -*-
import datetime
import locale
import subprocess
import signal
import time
import os
import sys
import platform
import requests
import re
import shlex
import threading
import atexit
import math
from ConfigParser import SafeConfigParser
from distutils import spawn
# 3rd party modules
import grovepi
from pyicloud import PyiCloudService        # pip install pyicloud

# Global var
home_dir = os.path.expanduser('~')
config_file = home_dir + '/.speakevents'
lock_file1 = '/tmp/speakEventsLockfile1'
lock_file2 = '/tmp/speakEventsLockfile2'
lock_file3 = '/tmp/speakEventsLockfile3'
mplayer_log = '/tmp/speakEventsMpLogfile'
sleep_time = 0.1

# Weather info for 'Kanto Plain'
weather_URL1 = 'http://www.tenki.jp/forecast/3/16/'

# Pinpoint weather info for 'Setagaya-ku'
weather_URL2 = 'http://www.tenki.jp/forecast/3/16/4410/13112-daily.html'

# iCloud account
userid = ''
passwd = ''

# Flag, turn radio on
radio_on = 0

# Normalized sound volume
vol_agqr = 0.03
vol_tko = 0.01
vol_norm = 0.60

# Init RGB LED's color
color_rgb = [0, 255, 0]

# Set GrovePi+ ports.
#
# If you use Encoder, update firmware to v1.2.6 with patch.
# And Encoder work only D2 port.
# encoderPort2 = 2
# encoderPort3 = 3

# Button port for iCloud
icloudBtnPort = 4

# Button port for radio
radioBtnPort = 5

# Button port for LED
lightBtnPort = 6

# Chainable RGB LED port
# if you use this with Encoder, update firmware and apply patch
rgbLEDPort = 7

# Number of chained RGB LED
num_of_leds = 1

# Normal LED port
feedbackLEDPort = 8

grovepi.pinMode(icloudBtnPort, 'INPUT')
grovepi.pinMode(radioBtnPort, 'INPUT')
grovepi.pinMode(lightBtnPort, 'INPUT')
grovepi.pinMode(rgbLEDPort, 'OUTPUT')
grovepi.pinMode(feedbackLEDPort, 'OUTPUT')

# Init Grove Encoder
atexit.register(grovepi.encoder_dis)
grovepi.encoder_en()
    
# test colors used in grovepi.chainableRgbLed_test()
# testColorBlack = 0   # 0b000 #000000
# testColorBlue = 1    # 0b001 #0000FF
# testColorGreen = 2   # 0b010 #00FF00
# testColorCyan = 3    # 0b011 #00FFFF
# testColorRed = 4     # 0b100 #FF0000
# testColorMagenta = 5 # 0b101 #FF00FF
# testColorYellow = 6  # 0b110 #FFFF00
# testColorWhite = 7   # 0b111 #FFFFFF

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
        print('====> atalk.sh がありません。')
        quit()
elif platform.system() == 'Darwin':
    if spawn.find_executable('/usr/bin/say'):
        speaker = '/usr/bin/say -r'
    else:
        print('====> say がありません。')
        quit()
else:
    quit()


# Internet Radio channels
radioChannels = [
    'rtmp://fms-base1.mitene.ad.jp/agqr/aandg22',
    'http://14023.live.streamtheworld.com/AFNP_TKO',
    'http://14093.live.streamtheworld.com/AFN_JOE',
    'http://4533.live.streamtheworld.com/AFN_PTK',
    'http://6073.live.streamtheworld.com/AFN_VCE',
    'http://14963.live.streamtheworld.com/AFN_FRE',
    ]


# Create simple color
def generate_rgb_color(v):
    t1 = math.cos(4 * math.pi * v)
    c = int(((-t1 / 2) + 0.5) * 255)
    
    if v >= 1.0:
        return (255, 0, 0)
    elif v >= 0.75:
        return (255, c, 0)
    elif v >= 0.5:
        return (c, 255, 0)
    elif v >= 0.25:
        return (0, 255, c)
    elif v >= 0:
        return (0, c, 255)
    else:
        return (0, 0, 255)


# Detect mplayer
def detect_mplayer():
    pid = 0
     
    ps_cmd = subprocess.Popen(
        ['ps', 'axw'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        close_fds=True,
        shell=False
        )
    out = ps_cmd.communicate()[0]
    
    for line in out.splitlines():
        if ('mplayer' in line and 'AFN' in line) \
                or ('mplayer -novideo' in line) \
                or ('rtmpdump' in line):
            pid = int(line.split(None, 1)[0])
    
    if pid > 0:
        return 1
    else:
        return 0


# Kill mplayer
def kill_mplayer():
    global color_rgb
    pid = 0
    
    ps_cmd = subprocess.Popen(
        ['ps', 'axw'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        close_fds=True,
        shell=False
        )
    out = ps_cmd.communicate()[0]
    
    for line in out.splitlines():
        if ('mplayer' in line and 'AFN' in line) \
                or ('mplayer -novideo' in line) \
                or ('rtmpdump' in line):
            pid = int(line.split(None, 1)[0])
            if pid > 0:
                os.kill(pid, signal.SIGTERM)
    
    if pid > 0 and os.path.exists(mplayer_log):
        os.remove(mplayer_log)
    
    # Turn Chainable RGB LED off
    color_rgb = [0, 0, 0]
    grovepi.storeColor(color_rgb[0], color_rgb[1], color_rgb[2])
    grovepi.chainableRgbLed_pattern(rgbLEDPort, thisLedOnly, 0)


# AFN360 procedure, play and stop
def start_radio(channel, doPlay):
    global color_rgb
    
    # create lock file
    f = open(lock_file2, 'w')
    f.close()
    
    if doPlay == 1:
        kill_mplayer()
        
        if channel > 5:
            channel = 2
        #     radio_timer.start()
        # else:
        #     radio_timer.cancel()
        
        # Turn Chainable RGB LED on
        x = (channel * 21) / 100.0
        (r, g, b) = generate_rgb_color(x)
        color_rgb = [r, g, b]
        grovepi.storeColor(r, g, b)
        grovepi.chainableRgbLed_pattern(rgbLEDPort, thisLedOnly, 0)
        print('====> color: %d, %d, %d') % (r, g, b)
        
        # If not found mplayer, run mplayer.
        print('====> start Radio channel: %s.') % radioChannels[channel]
        if channel == 0:
            # Bad script. But anti zombie process.
            cmd = "nohup sh -c \"rtmpdump --live -r %s" \
              " | mplayer -novideo -af volnorm=2:%s - > /dev/null 2>&1\"" \
              " > /dev/null 2>&1 &" % (radioChannels[channel], vol_agqr)
            subprocess.call(cmd, shell=True)
        else:
            # Bad script. But anti zombie process.
            if channel == 1:
                cmd = "nohup mplayer -af volnorm=2:%s %s" \
                  " > /dev/null 2>&1 &" % (vol_tko, radioChannels[channel])
            else:
                cmd = "nohup mplayer -af volnorm=2:%s %s" \
                  " > /dev/null 2>&1 &" % (vol_norm, radioChannels[channel])
            subprocess.call(cmd, shell=True)
            # subprocess.Popen(
            #     cmd.split(),
            #     stdout=open('/dev/null', 'w'),
            #     stderr=open(mplayer_log, 'a'),
            #     preexec_fn=os.setpgrp
            #     )
    else:
        print('====> stop Radio')
        kill_mplayer()
    
    # Remove lock file.
    os.remove(lock_file2)
    
    # Turn feedback LED off
    grovepi.digitalWrite(feedbackLEDPort, 0)


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
    global weather_URL1
    global weather_URL2
    global userid
    global passwd
    
    if not os.path.isfile(config_file):
        print u'====> config file not found.'
        quit()
    
    parser = SafeConfigParser()
    parser.read(config_file)
    
    userid = parser.get('account', 'user')
    assert isinstance(userid, str)
    
    passwd = parser.get('account', 'pass')
    assert isinstance(passwd, str)
    
    w1 = parser.get('weatherurls', 'weather1')
    if w1:
        weather_URL1 = w1
        assert isinstance(weather_URL1, str)
    else:
        assert isinstance(weather_URL1, str)
    
    w2 = parser.get('weatherurls', 'weather2')
    if w2:
        weather_URL2 = w2
        assert isinstance(weather_URL2, str)
    else:
        assert isinstance(weather_URL2, str)


# get iCloud Calendar data.
def get_iccdata():
    api = PyiCloudService(userid, passwd)
    
    if api:
        d = datetime.datetime.today()
        from_dt = datetime.datetime(d.year, d.month, d.day)
        to_dt = datetime.datetime(d.year, d.month, d.day)
        iccEvents = api.calendar.events(from_dt, to_dt)
        
        return iccEvents
    else:
        print('====> api is null.')
        return None


# Get Weather Info 1
def get_weatherinfo1(url):
    htmlTagPattern = re.compile(r'<[^>]*?>')

    # Get HTML strings
    req = requests.get(url)
    htmlString = req.text
    delStrPattern = r'<h2 class="sub_title">(.*)</p>'
    matches = re.finditer(delStrPattern, htmlString)
    
    for match in matches:
        w = htmlTagPattern.sub('', match.groups()[0])
    
    if w:
        return w
    else:
        return None


# Get Weather Info 2
def get_weatherinfo2(url):
    info = []
    htmlTagPattern = re.compile(r'<[^>]*?>')
    
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
    
    # In this step info[] has began following,
    # [気温, N度, N度]
    for match in matches:
        tempN = htmlTagPattern.sub('', match.groups()[0])
        info.append(tempN + u'度')
    
    # Get chance of rain.
    rainPattern = ur'<td>(.*)</td>'
    matches = re.finditer(rainPattern, todaysHtml)
    info.append(u'降水確率')
    
    # In this step info[] has began following,
    # [気温, N度, N度, 降水確率, N%, N%, N%, N%]
    for match in matches:
        rainN = htmlTagPattern.sub('', match.groups()[0])
        if rainN == '---':
            rainN = u'なし'
        info.append(rainN)
    
    # Finally info[] has began following,
    # [気温,最高,N度,最低,N度,降水確率,0時6時,N%,6時12時,N%,12時18時,N%,18時24時,N%]
    if len(info) == 8:
        info.insert(1, u'最高気温')
        info.insert(3, u'最低気温')
        info.insert(6, u'0時6時')
        info.insert(8, u'6時12時')
        info.insert(10, u'12時18時')
        info.insert(12, u'18時24時')
        return info
    else:
        return None


#
def loop_day(e):
    # 一日分のループ
    for event in e:
        # 個別イベントのループ
        for key, value in event.items():
            if key == 'startDate':
                hour = value[4]
                min = value[5]
                
                if hour == 0 and min == 0:
                    eventTime = u'終日'
                else:
                    eventTime = str(hour) + u'時' + str(min) + u'分から'
                
                # print eventTime
                cmd = speaker + ' 130 "' + eventTime + '"'
                subprocess.call(cmd.split(), shell=False)
            
            if key == 'endDate':
                hour = value[4]
                min = value[5]
                
                if hour == 0 and min == 0:
                    eventEndTime = u'、'
                else:
                    eventEndTime = str(hour) + u'時' + str(min) + u'分まで'
                
                # print eventEndTime
                cmd = speaker + ' 130 "' + eventEndTime + '"'
                subprocess.call(cmd.split(), shell=False)
            
            if key == 'title':
                eventTitle = value + u'の予定があります。'
                # print eventTitle
                cmd = speaker + ' 100 "' + eventTitle + '"'
                subprocess.call(cmd.split(), shell=False)
                time.sleep(1)


# speak events.
def speak_events():
    # create lock file
    f = open(lock_file1, 'w')
    f.close()
    
    # Get config
    get_config()
    
    # Speak Weather 1
    WeatherInfo1 = get_weatherinfo1(weather_URL1)
    if WeatherInfo1:
        cmd = speaker + ' 130 "' + WeatherInfo1 + '"'
        subprocess.call(cmd.split(), shell=False)
        time.sleep(1)
    
    # Speak Weather 2
    WeatherInfo2 = get_weatherinfo2(weather_URL2)
    if WeatherInfo2:
        for info in WeatherInfo2:
            cmd = speaker + ' 100 "' + info + '"'
            subprocess.call(cmd.split(), shell=False)
        
        time.sleep(1)
    
    # Speak Events
    events = get_iccdata()
    if events:
        events2 = sorted(events, key=lambda x:x['startDate']) # sort startDate
        loop_day(events2)
        endTalk = u'忘れ物はありませんか。以上'
        cmd = speaker + ' 100 "' + endTalk + '"'
        subprocess.call(cmd.split(), shell=False)
    else:
        # 一日分のイベントが空
        talk = u'本日の予定はありません。以上'
        cmd = speaker + ' 120 "' + talk + '"'
        subprocess.call(cmd.split(), shell=False)
    
    # Remove lock file.
    os.remove(lock_file1)
    
    # Turn feedback LED off
    grovepi.digitalWrite(feedbackLEDPort, 0)


def return_color():
    global color_rgb
    
    # Turn LED off
    grovepi.digitalWrite(feedbackLEDPort, 0)

    # Turn RGB LED off
    grovepi.storeColor(color_rgb[0], color_rgb[1], color_rgb[2])
    grovepi.chainableRgbLed_pattern(rgbLEDPort, thisLedOnly, 0)

    # Remove lock file.
    os.remove(lock_file3)


class MyThreading(object):
    def __init__(self, interval, function, args=[], kwargs={}):
        self._interval = interval
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def start(self):
        t = threading.Timer(
                self._interval,
                self._function,
                *self._args,
                **self._kwargs
                )
        t.start()


# main
if __name__ == '__main__':
    # Init LED
    grovepi.digitalWrite(feedbackLEDPort, 0)
    
    # Init Chainable RGB LED
    grovepi.chainableRgbLed_init(rgbLEDPort, num_of_leds)
    
    # Create threading object
    # radio_timer = MyThreading(5400, kill_mplayer)
    rgbled_timer = MyThreading(40, return_color, ())
    
    # Init mplayer
    kill_mplayer()
    
    # start up blink
    startup_blink = [7,6,5,4,3,2,1,0,7]
    for i in startup_blink:
        grovepi.chainableRgbLed_test(rgbLEDPort, num_of_leds, i)
        time.sleep(.1)
    
    [new_val, encoder_val] = grovepi.encoderRead()
    
    if new_val == 0:
        color_rgb = [0, 0, 0]
    else:
        color_rgb = [255, 0, 0]

    grovepi.storeColor(color_rgb[0], color_rgb[1], color_rgb[2])
    grovepi.chainableRgbLed_pattern(rgbLEDPort, thisLedOnly, 0)
    
    while True:
        try:
            # Encoder
            if radio_on == 1:
                [new_val, encoder_val] = grovepi.encoderRead()
                if new_val:
                    print('====> Encoder: %d') % encoder_val
                    if os.path.exists(lock_file2):
                        print('====> Locking...')
                    else:
                        start_radio(encoder_val, radio_on)
            
            # Button for speaking self iCloud Calendar
            if grovepi.digitalRead(icloudBtnPort) == 1:
                print('====> Button: D%d') % icloudBtnPort
                
                # Turn feedback LED on
                grovepi.digitalWrite(feedbackLEDPort, 1)
                
                # Run speak_events
                if os.path.exists(lock_file1):
                    print('====> Locking...')
                else:
                    speak_events()
            
            # Button for turning Radio on/off
            if grovepi.digitalRead(radioBtnPort) == 1:
                print('====> Button: D%d') % radioBtnPort
                
                # Turn feedback LED on
                grovepi.digitalWrite(feedbackLEDPort, 1)
                
                # Detect mplayer
                radio_on = detect_mplayer()
                print('====> radio_on: %d') % radio_on
                
                # Run internet radio
                if os.path.exists(lock_file2):
                    print('========> Locking...')
                else:
                    if radio_on == 0:
                        [new_val, encoder_val] = grovepi.encoderRead()
                        print('========> Encoder: %d') % encoder_val
                        radio_on = 1
                        start_radio(encoder_val, radio_on)
                    else:
                        radio_on = 0
                        start_radio(0, radio_on)
            
            # Button for blinking RGB LED
            if grovepi.digitalRead(lightBtnPort) == 1:
                print('====> Button: D%d') % lightBtnPort

                # Turn feedback LED on
                grovepi.digitalWrite(feedbackLEDPort, 1)

                # Run internet radio
                if os.path.exists(lock_file3):
                    print('====> Locking...')
                else:
                    # create lock file
                    f = open(lock_file3, 'w')
                    f.close()

                    # Blink RGB LED
                    grovepi.storeColor(255, 255, 255)
                    grovepi.chainableRgbLed_pattern(rgbLEDPort, thisLedOnly, 0)
                    rgbled_timer.start()
            
            # Loop interval time
            time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print('====> ctrl + c')
            color_rgb = [0, 0, 0]
            grovepi.storeColor(color_rgb[0], color_rgb[1], color_rgb[2])
            grovepi.chainableRgbLed_pattern(rgbLEDPort, thisLedOnly, 0)
            grovepi.digitalWrite(feedbackLEDPort, 0)
            quit()
        
        except IOError:
            print('====> IO Error.')
