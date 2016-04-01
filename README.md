# speakEvents.py

## 説明
Raspberry Pi に BLE やタクトスイッチなどの何かしらのアクションがあった時、iCloud から当日の予定を取得し声でお知らせします。声でお知らせしてくれるので、朝、何かしながら予定の確認をすることができます。

## 必要なもの
1. pyicloud
2. AquesTalkPi
3. wrapper of AquesTalkPi (eg, atalk.sh)

## 導入
1. sudo pip install pyicloud
2. Download AquesTalkPi and unzip.
3. vi atalk.sh
4. Download speakEvent.py (this script).
5. touch ~/.pyicloud && chmod 600 ~/.pyicloud
6. vi ~/.pyicloud
7. Adjust speakEvent.py (eg, path etc...)

.pyicloud format
```
[account]
user = your apple id
pass = your apple id password
```

## ライセンス
MIT

## 著者
tkumata
