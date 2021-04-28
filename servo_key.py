import pigpio
import time
import datetime
import pytz
import csv
import os


class key():
    def __init__(self):
        self.swpin = 3  # MOS-FET制御信号ピン
        self.pin = 14   # パルス信号ピン
        self.pi = pigpio.pi()

    # 施錠
    def lock(self):
        # 手動操作閉鎖
        self.pi.write(self.swpin, 1)
        time.sleep(0.5)
        # 駆動
        self.pi.set_servo_pulsewidth(self.pin, 1445)
        # 手動操作開放
        self.pi.write(self.swpin, 0)
        time.sleep(0.5)

        self.writelog("Lock")  # ログ書き込み

    # 解錠
    def unlock(self):
        # 手動操作閉鎖
        self.pi.write(self.swpin, 1)
        time.sleep(0.5)
        # 駆動
        self.pi.set_servo_pulsewidth(self.pin, 520)
        # 手動操作開放
        self.pi.write(self.swpin, 0)
        time.sleep(0.5)

        self.writelog("Unlock")  # ログ書き込み

    # ログ書き込み
    def writelog(self, str):
        with open('/var/www/html/log/log.csv', 'a') as f:
            now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
            writer = csv.writer(f)
            writer.writerow([now.strftime("%Y/%m/%d %H:%M:%S"), str])
    
    # ログ読み込み
    def readlog(self):
        # ログ未存在なら作成
        if not os.path.exists('/var/www/html/log/log.csv'):
            with open('/var/www/html/log/log.csv', 'w') as f:
                os.chmod('/var/www/html/log/log.csv', 0o777)  # フルコントロール権限

                writer = csv.writer(f)
                writer.writerow(['----/--/-- --:--:--', "Lock"])

        r = {}
        # ログ読み込み
        with open('/var/www/html/log/log.csv', 'r') as f:
            reader = csv.reader(f)
            logs = [row[0] + "\t" + row[1] for row in reader]

        # 現在のステータス取得
        if "Lock" in logs[-1]:
            r['status'] = 1
        elif "Unlock" in logs[-1]:
            r['status'] = 0

        logs.reverse()
        r['log'] = logs

        # ログ行数が11行以上なら削除
        if len(logs) > 10:
            os.remove('/var/www/html/log/log.csv')  # 消去
            # 直近のログ１つのみ書き込み
            with open('/var/www/html/log/log.csv', 'w') as f:
                os.chmod('/var/www/html/log/log.csv', 0o777)  # フルコントロール権限

                writer = csv.writer(f)
                writer.writerow(logs[0].split('\t'))

        return r
