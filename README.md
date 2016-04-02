# speakEvents.py

## 説明
Raspberry Pi に BLE やタクトスイッチなどの何かしらのアクションがあった時、iCloud から当日の予定を取得し声でお知らせします。声でお知らせしてくれるので、朝、何かしながら予定の確認をすることができます。

※アクション部分は各自で作ってください。

## 必要なもの
1. pyicloud
2. AquesTalkPi
3. wrapper of AquesTalkPi (eg, atalk.sh)

## 導入
1. sudo pip install pyicloud
2. Download AquesTalkPi and unzip.
3. Create wrapper (eg, vi atalk.sh).
4. Download speakEvent.py (this script).
5. touch ~/.pyicloud && chmod 600 ~/.pyicloud && vi ~/.pyicloud
6. Adjust speakEvent.py (eg, path etc...)

- .pyicloud format
```
[account]
user = your apple id
pass = your apple id password
```

## ライセンス
MIT

## 著者
tkumata
