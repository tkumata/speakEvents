# speakEvents.py

## 説明
Raspberry Pi 3 に BLE やタクトスイッチなどの何かしらのアクションがあった時、iCloud から当日の予定を取得し声でお知らせします。声でお知らせしてくれるので、朝、何かしながら予定の確認をすることができます。

GrovePi+ の D2 port は iCloud Calendar を読み上げます。

GrovePi+ の D3 port は AFN Toyko を再生します。再生中だった場合、停止します。

RPi3 を再起動してもこのプログラムが動くように sh 追加しました。これで単体で機能します。

## 必要なハード
1. Raspberry Pi 3
2. GrovePi+
3. Two buttons (Connect D2 and D3)

## 必要なソフト
1. OS: Raspbian for robots
2. Python module: pyicloud
3. AquesTalkPi
4. wrapper of AquesTalkPi (eg, atalk.sh)

## 導入
1. sudo pip install pyicloud
2. Download AquesTalkPi and unzip.
3. Create wrapper (eg, vi atalk.sh).
4. git clone git@github.com:tkumata/speakEvents.git.
5. touch /home/pi/.pyicloud && chmod 600 /home/pi/.pyicloud && vi /home/pi/.pyicloud
6. Adjust speakEvent.py (eg, path etc...)
7. sudo cp speakEventsService.sh /etc/init.d/

- example atalk.sh
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

- /home/pi/.pyicloud format
```
[account]
user = your apple id
pass = your apple id password
```

## ライセンス
MIT

## 著者
tkumata
