from PIL import Image
import os
import io
import urllib


cnt = 0
while True:
    # カメラサーバー(ESP32)からカメラ画像を取得
    file = io.BytesIO(urllib.request.urlopen('http://192.168.1.12').read())
    frame = Image.open(file)

    # 保存
    frame.save(os.path.join('./img/', 'log' + str(cnt) + '.jpg'))
    if cnt == 1200:
        break
    cnt += 1
