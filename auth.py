import io
import urllib
from urllib.request import urlopen

from PIL import Image
import numpy as np
import cv2

import sys
import os
import time

import subprocess as sp
from socket import *

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # TFメッセージ非表示

import tensorflow as tf

import servo_key

# 顔認証
class FaceaddrAuth():
    def __init__(self):
        model_file = os.path.abspath("./model/face_recog_tf.tflite") # モデル
        haar_cascade = os.path.abspath("./model/haar_cascade.xml")  # haar_cascade

        # 顔検出器のセット
        self.detector = cv2.CascadeClassifier(haar_cascade)

        # モデルのセット
        self.interpreter = tf.lite.Interpreter(model_path=model_file)
        self.interpreter.allocate_tensors()

        # 入力/出力のtensor取得
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def run(self):
        # ESP32から画像取得
        file = io.BytesIO(urllib.request.urlopen('http://192.168.1.12').read())
        frame = Image.open(file)
        frame = np.array(frame, dtype=np.uint8)

        # 顔検出
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray)

        # 顔未検出
        if len(faces) == 0:
            return False

        # 顔検出時
        for (x, y, h, w) in faces:
            # 顔が小さすぎる
            if h < 50 and w < 50:
                return False

            # 画像処理
            face = gray[y:y + h, x:x + w]
            face = Image.fromarray(face)
            face = np.asarray(face.resize((96, 96)), dtype=np.float32)
            face = face / 255
            face = face[np.newaxis, :, :]
            face = np.repeat(face[..., np.newaxis], 3, -1)
            face = tf.convert_to_tensor(face, np.float32)
            
            # 顔識別
            self.interpreter.set_tensor(self.input_details[0]['index'], face)
            self.interpreter.invoke()
            y = self.interpreter.get_tensor(self.output_details[0]['index'])

            c = np.argmax(y)
            if c == 0: # 認証OK
                return True
            else:   # 認証NG
                return False

        return False

# MACアドレス認証
class MacaddrAuth():
    def __init__(self):
        # スマホ情報
        ip = "192.168.1.*"
        macaddr = "**:**:**:**:**:**"
    
        self.ping = "ping " + ip + " -c 1 -s 1 > /dev/null"
        self.arp_serch = "arp -a | grep " + macaddr
        self.arp_delete = "arp -d " + ip

    def run(self):
        # ping送信
        prc = sp.run(self.ping, shell=True)
        # ターゲットMACアドレスの存在確認
        res = sp.run(self.arp_serch, shell=True, stdout=sp.PIPE, text=True)
        # ターゲットMACアドレス消去
        pre = sp.run(self.arp_delete, shell=True)

        if res.returncode == 0: # 認証OK
            return True
        else:   # 認証NG
            return False

class UDP():
    def __init__(self):
        # Raspberry Pi側情報
        raspIP = "192.168.1.8"
        raspPort = 6100
        raspAddr = (raspIP, raspPort)

        # ESP側情報
        espIP = "192.168.1.12"
        espPort = 6000
        self.espAddr = (espIP, espPort)

        self.BUFSIZE = 128

        # 送信/受信ソケット
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(raspAddr)
        self.socket.settimeout(0.1)

    # 施錠フラグ送信 (UDP)
    def sendUDP(self, data):
        data = data.encode("utf-8")
        self.socket.sendto(data, self.espAddr)

    # PIR反応フラグ受信 (UDP)
    def receiveUDP(self):
        data, addr = self.socket.recvfrom(self.BUFSIZE)
        return data, addr

def main():
    udp = UDP()

    fa = FaceaddrAuth()
    ma = MacaddrAuth()

    KEY = servo_key.key()

    while True:
        r = KEY.readlog()   # ログ読み込み
        
        # 施錠状態であれば
        if r['status'] == 1:
            try:
                # 施錠フラグ送信
                udp.sendUDP("lock")
                # PIR反応フラグ受信
                data, _ = udp.receiveUDP()
            except timeout as err:
                continue

            # 人を検知
            if data.decode():
                # 顔認証
                fa_result = fa.run()

                # 本人の顔であれば
                if fa_result:
                    # MACアドレス認証
                    ma_result = ma.run()
                    # 本人の所有するスマホのMACアドレスならば
                    if ma_result:
                        # 解錠
                        KEY.unlock()

if __name__ == '__main__':
    main()

