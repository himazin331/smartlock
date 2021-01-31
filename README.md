# セキュアなスマートロックを作りたい

## 概要
**顔認証**(生体)とスマホの**MACアドレス認証**(所有)の二要素認証で解錠するスマートロックをつくる。
また、遠隔でも解錠/施錠できるようにWebアプリケーションを通じて制御できるようにする。

玄関ドアの外側に**TTGO T-camera**(人感センサー付カメラ)を取り付ける。モバイルバッテリーなどで供給する。(ドアの構造上及びコンセントがないため)

消費電力を抑えるために、施錠状態かつ人を感知したときにのみ認証を試みる。

スマホのMACアドレスは自宅WiFiに自動接続されたときにarpコマンドにより取得する。

## システム構成
![システム構成図](https://user-images.githubusercontent.com/63523973/106396232-1190ec80-644a-11eb-8510-341154f40771.jpg)

 - **Webアプリケーション**
AAA.himazin331.comはCGI用FQDN。BBB.himazin331.comはラズパイ用FQDN(サブドメインは秘匿)
AAA.himazin331.comはSSL/TLS暗号化させMixed Content回避。BBB.himazin331.comはDDNSによって自宅のグローバルIPと紐付ける。

- **認証**
TTGO T-cameraはSTAモードで稼働させ自宅LANに接続させる。
UDP通信では、ラズパイがT-cameraに施錠状態であることを伝える、T-cameraがラズパイに人を感知したことを伝えることをする。
HTTP通信ではラズパイがT-cameraのカメラサーバーにリクエストし、カメラ画像を取得する。

BBB.himazin331.comをSSL/TLS暗号化させれば楽なのだが、私のネットワーク環境はIPv6 IPoE(IPv4 over IPv6)のため80, 443番ポートを開放できず、Let's EncryptのHTTP-01チャレンジができなかった。また、ラズパイ - Azure間をOpenVPNで通信の秘匿化を図ったが、なぜかWebページが表示されなくなってしまったので断念。

## シーケンス図

### Webアプリケーション
![Webアプリケーション-シーケンス図](https://user-images.githubusercontent.com/63523973/106396761-579b7f80-644d-11eb-9432-8e47d485c272.png)

### 認証
![認証 - シーケンス図](https://user-images.githubusercontent.com/63523973/106396763-59fdd980-644d-11eb-8e1c-bc4c25921834.jpeg)

## 回路図
![回路図](https://user-images.githubusercontent.com/63523973/105632853-be8ec680-5e98-11eb-89c7-2dd93732de1d.png)

入力コンデンサ0.033μFとあるが、0.33μFが適切である。([datasheet](https://akizukidenshi.com/download/ds/st/l78.pdf)より)
しかし、手違いで0.033μFのコンデンサ使い実装してしまった。
一応、動作に影響はないが差し替える予定。

## 実体配線図
![実体配線図](https://user-images.githubusercontent.com/63523973/105632856-bfbff380-5e98-11eb-8412-6171d1064d21.png)

当初はGPIO 4番を使う予定だったが、実装中に短絡して不能になってしまったため、GPIO 14番に変更。

## 使用ハードウェア
- Azure VM (米国西部2 CentOS 7.8.2003 Standard B1s (1 vcpu 数、1 GiB メモリ))
- Raspberry Pi Zero WH
- MG996R ([datasheet](https://akizukidenshi.com/download/ds/towerpro/mg996r.pdf))
- 9V-2A ACアダプタ
- 三端子レギュレータ L7806CV ([datasheet](https://akizukidenshi.com/download/ds/st/l78.pdf))
- MOS-FET INK021ABS1-T112 ([datasheet](https://akizukidenshi.com/download/ds/isahaya/INK021ABS1_J.pdf))
- その他電子部品
- TTGO T-Camera ESP32 WROVER & PSRAM Camera Module ([商品リンク](https://www.amazon.co.jp/gp/product/B07PPR8Z2S/))
- 適当なモバイルバッテリー
- 3Dプリンタ (ガワ造形)

## 使用言語
- Python
- C/C++
- HTML/CSS
- Javascript

## 使用ライブラリ
- Apache
- Ajax
- Tensorflow, Tensorflow Lite
- pigpio
- OpenCV
- [T-camera Demo Program](https://github.com/lewisxhe/esp32-camera-series
)
