# ゆっくりが予定や天気情報を喋ったり、AFN 360 を再生したりする IoT


## 説明
Raspberry Pi 3 (以下 RPi3) に BLE やボタンなどから何かしらの入力があった時、tenki.jp の天気情報や iCloud 内の当日の全予定を音声でお知らせします。音声なので忙しい場合でも、何かしながら予定の確認ができます。また、付録機能として AFN 360 の再生ができます。

[動画](images/IMG0054.m4v)

今回はお気楽極楽に、入力として GrovePi+ を使うことにしました。GrovePi+ の D2, D3 port にボタンを接続します。D2 port のボタンは天気情報と iCloud Calendar を読み上げ、D3 port のボタンは AFN 360 を再生します。もし既に再生中だった場合、停止します。

RPi3 を再起動してもこのプログラムが動くように sh を追加しました。なのでこれ単体で機能します。

再生のたびに AFN のチャンネルを変更するようにしました。具体的には...

再生(Tokyo)、停止、再生(Joe Radio)、停止、再生(Power Talk)、停止、再生(The Voice)、停止、再生(Freedom)、停止、再生(Tokyo)...

となります。

[![the thing](images/IMG0047.png)](images/IMG0054.m4v)


## 必要なハード
1. Raspberry Pi (Well, I use RPi3 model B.)
2. GrovePi+
3. Two buttons for Grove


## 必要なソフト
1. OS として [Raspbian for Robots](http://www.dexterindustries.com/howto/install-raspbian-for-robots-image-on-an-sd-card/) (RPi3 と素の Raspbian の組み合わせだと Grove の反応が超絶イマイチで、粗悪品のボタンを掴んだか？って勘違いするほどです。ハマりました。2016/04/12 時点で GrovePi と RPi3 の組み合わせを使うなら OS は Raspbian for Robots がオススメです。RPi2 は分かりません。)
2. Python module の pyicloud
3. テキスト読み上げソフトとして [AquesTalkPi](http://www.a-quest.com/products/aquestalkpi.html) (AquesTalkPi なら日本語も喋ってくれるし、英語もアルファベット読みにならないので。)
4. Wrapper for AquesTalkPi (eg, atalk.sh) (AquesTalkPi は wav を作るだけなので aplay で再生するようにラッパを作成する必要があります。)


## 導入
1. Setup [Raspbian for Robots](http://www.dexterindustries.com/howto/install-raspbian-for-robots-image-on-an-sd-card/).
2. sudo pip install pyicloud
3. Download [AquesTalkPi](http://www.a-quest.com/products/aquestalkpi.html) and unzip.
4. Create wrapper (eg, vi atalk.sh).
5. git clone git@github.com:tkumata/speakEvents.git
6. touch /home/pi/.speakevents && chmod 600 /home/pi/.speakevents && vi /home/pi/.speakevents (Please see below.)
7. Adjust "speakEvents/speakEvents.py" (eg, path etc...)
8. sudo cp speakEvents/speakEventsService.sh /etc/init.d/
9. sudo update-rc.d speakEventsService.sh defaults
10. sudo /etc/init.d/speakEventsService.sh start


- example atalk.sh

AquesTalkPi が作った wav データを再生する wrapper の例です。

```
#!/bin/bash
aquestalkpi=/home/pi/bin/aquestalkpi/AquesTalkPi
var=`$aquestalkpi "$@" | base64; echo ":${PIPESTATUS[0]}"`
ret=(${var##*:})
data=${var%:*}
if [ $ret -eq 0 ]; then
  echo $data | base64 --decode --ignore-garbage | aplay -q
else
  echo $data | base64 --decode --ignore-garbage
  exit $ret
fi
```


- /home/pi/.speakevents format

pyicloud を使うための設定ファイルの形式です。天気情報は tenki.jp のみ対応しています。

```
[account]
user = yourappleid@example.com
pass = your_appleid_password

[weatherurls]
weather1 = http://www.tenki.jp/forecast/3/16/
weather2 = http://www.tenki.jp/forecast/3/16/4410/13112-daily.html
```


## 予定
- ロータリーかスライダーで AFN のチャンネルを選択できるようにしたい。
- 折角の RPi3 なので BLE でコントロールできるようにしたい。
- ニュースヘッドラインも追加したい。


## ライセンス
MIT


## 著者
tkumata
