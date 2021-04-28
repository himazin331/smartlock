#!/usr/bin/python3
import sys
import json
import servo_key

status = ""
status = sys.stdin.readline()  # POSTデータ

k = servo_key.key()
if status != "":  # 施錠/解錠
    print('Content-Type: text/html;')
    print('Access-Control-Allow-Methods: POST;\nAccess-Control-Allow-Origin: https://smartlk.himazin331.com\n')

    if "0" in status:
        k.unlock()
    else:
        k.lock()
else:  # ステータス&ログ取得
    print('Content-Type: application/json;')
    print('Access-Control-Allow-Methods: POST;\nAccess-Control-Allow-Origin: https://smartlk.himazin331.com\n')

    result = k.readlog()
    print(json.dumps(result))
