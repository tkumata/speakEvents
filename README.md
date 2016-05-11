# ゆっくりが予定や天気情報を喋ったり、AFN 360 を再生したりする IoT


## 説明
Raspberry Pi 3 (以下 RPi3) に BLE やボタンなどから何かしらの入力があった時、以下のことをします。

- tenki.jp の天気情報を音声でお知らせ
- iCloud 内の当日の全予定を音声でお知らせ
- AFN 360 の再生 (RGB LED でチャンネル毎に色を変える)

音声なので忙しい場合でも、何かしながら予定の確認ができます。

今回はお気楽極楽に、入力として GrovePi+ を使うことにしました。GrovePi+ の

| Port | Device            | Role                                   | Notes   |
|------|:-----------------:|:--------------------------------------:|:--------|
| D2   | Encoder           | インターネットラジオのチャンネルの変更 | D2 only | 
| D4   | Button            | 天気情報と iCloud Calendar を読み上げ  ||
| D5   | Button            | インターネットラジオの再生、停止       ||
| D7   | Chainable RGB LED | チャンネルの表現                       ||
| D8   | Normal LED        | ボタンを押した時のフィードバック用     ||

AFN のチャンネルは Encoder の...

| Step | Channnel   | Color        | Timer |
|------|:----------:|:------------:|:------|
| 0    | 超 A&G     | 何か一意な色 | None  |
| 1    | Tokyo      | 何か一意な色 | None  |
| 2    | Joe Radio  | 何か一意な色 | None  |
| 3    | Power Talk | 何か一意な色 | None  |
| 4    | The Voice  | 何か一意な色 | None  |
| 5    | Freedom    | 何か一意な色 | None  |
| 6-24 | Joe Radio  | 何か一意な色 | ~~~one hour~~~ |

となります。色は配列の順番を種として特定のアルゴリズムで一意な色を自動的に生成されます。

[![the thing](images/IMG0047.png)](images/IMG0054.m4v)


## 必要なハード
1. Raspberry Pi 3
2. GrovePi+ (IMPORTANT!! Firmware is v1.2.5 over and apply following patch.)
3. Two buttons for Grove (D4, D5)
4. Chainable RGB LED (D7)
5. LED (D8)
6. Encoder (D2) (IMPORTANT!! Grove Encoder works on D2 port only.)


## 必要なソフト
1. OS として [Raspbian for Robots](http://www.dexterindustries.com/howto/install-raspbian-for-robots-image-on-an-sd-card/) (RPi3 と素の Raspbian の組み合わせだと Grove の反応が超絶イマイチで、粗悪品のボタンを掴んだか？って勘違いするほどです。ハマりました。2016/04/12 時点で GrovePi+ と RPi3 の組み合わせを使うなら OS は Raspbian for Robots がオススメです。RPi2 は分かりません。)
2. Python module の pyicloud
3. テキスト読み上げソフトとして [AquesTalkPi](http://www.a-quest.com/products/aquestalkpi.html) (AquesTalkPi なら日本語も喋ってくれるし、英語もアルファベット読みにならないので。)
4. Wrapper for AquesTalkPi (eg, atalk.sh) (AquesTalkPi は wav を作るだけなので aplay で再生するようにラッパを作成する必要があります。)
5. Firmware which patched v1.2.5 or patched v1.2.6.


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


## その他
* example atalk.sh

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


* /home/pi/.speakevents format

pyicloud を使うための設定ファイルの形式です。天気情報は tenki.jp のみ対応しています。

```
[account]
user = yourappleid@example.com
pass = your_appleid_password

[weatherurls]
weather1 = http://www.tenki.jp/forecast/3/16/
weather2 = http://www.tenki.jp/forecast/3/16/4410/13112-daily.html
```


* Firmware patch for v1.2.6

Encoder と Chainable RGB LED を同時に使うにはファームウェアにパッチ当てないといけません。パッチは私が作ったものでちゃんとした検証をしていませんのでご留意ください。「Encoder 使わないよ」と言う場合はファームウェアをいじらなくてもいいです。また、Encoder だけ使う場合はパッチを当てない v1.2.5 以上が必要です。

```
--- /home/pi/Desktop/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6/grove_pi_v1_2_6.ino   2016-04-23 20:35:48.636875637 +0900
+++ src/grove_pi_v1_2_6.ino 2016-05-04 09:09:57.028214361 +0900
@@ -96,7 +96,7 @@ int j;
 void loop()
 {
   long dur,RangeCm;
-  if(index==4)
+  if(index==4 && flag==0)
   {
     flag=1;
     //IR reciever pin set command
```


* Compile firmware v1.2.6 and install

```
$ sudo pip install ino
$ mkdir firmware && cd firmware
$ ino init
$ rm src/sketch.ino
$ cp -a ~/Desktop/GrovePi/Firmware/Source/v1.2/grove_pi_v1_2_6/* src/
(in this step apply patch.)
$ ino list-models
$ ino build -m atmega328
$ cd .build/atmega328
$ avrdude -c gpio -p m328p -U flash:w:firmware.hex
```


## 予定
- ~~~ロータリーかスライダーで AFN のチャンネルを選択できるようにしたい。~~~
- 折角の RPi3 なので BLE でコントロールできるようにしたい。
- ニュースヘッドラインも追加したい。
- ~~~AFN 以外のネットラジオも追加したい。~~~
- ~~~色。~~~


## 過去の版
- [ver2](https://github.com/tkumata/speakEvents/tree/ver2x)
- [ver1](https://github.com/tkumata/speakEvents/tree/ver1x)


## ライセンス
MIT


## 著者
tkumata
