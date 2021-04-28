import cv2
import os
import mimetypes
import tensorflow as tf
import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # TFメッセージ非表示


# 動画->画像変換
def video2img(imgs_dir):
    print("___Converting video to image...")

    for c in os.listdir(imgs_dir):
        d = os.path.join(imgs_dir, c)  # 動画パス
        print("Video file: {}".format(d))

        # 対応MIMEタイプ -> video
        mime = mimetypes.guess_type(c)
        # キャッシュファイルをスルー
        if mime[0] is None:
            print("Unsupported file extension")
            continue
        elif 'video' not in mime[0]:  # videoでないものはスルー
            print("Unsupported file extension")
            continue

        # 動画読み込み
        mv = cv2.VideoCapture(d)
        for f in range(int(mv.get(cv2.CAP_PROP_FRAME_COUNT)) - 1):
            # フレーム取得
            _, frame = mv.read()

            # 保存
            print(imgs_dir + "\\" + c + str(f) + ".jpg")
            cv2.imwrite(imgs_dir + "\\" + c + str(f) + ".jpg", frame)

        mv.release()
    print("___Successfully completed")


# 顔領域切り取り
def face_crop(imgs_dir, out_dir, img_size, channel, index, HAAR_FILE):
    print("___Cropping out face from image...")

    # 正解データフォルダ作成
    true_dir = os.path.join(out_dir, "true")
    os.makedirs(true_dir, exist_ok=True)
    # Haar-Like特徴量Cascade型分類器の読み込み
    cascade = cv2.CascadeClassifier(HAAR_FILE)
    
    # データ加工
    for img_name in os.listdir(imgs_dir):
        print("Image file: {}".format(img_name))
        
        # 対応MIMEタイプ -> image
        mime = mimetypes.guess_type(img_name)
        # キャッシュファイルをスルー
        if mime[0] is None:
            print("Unsupported file extension")
            continue
        elif 'image' not in mime[0]:  # imageでないものはスルー
            print("Unsupported file extension")
            continue

        img_path = os.path.join(imgs_dir, img_name)
        img = cv2.imread(img_path)  # データ読み込み
        
        # チャンネル数 -> 1
        if channel == 1:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # グレースケール変換
        face = cascade.detectMultiScale(img)  # 顔を検出

        # 顔が検出されなかったら
        if len(face) == 0:
            print("Face not found.")
        else:
            for n in range(len(face)):
                # X,Y座標、幅/高さ取得
                x = face[n][0]
                y = face[n][1]
                w = face[n][2]
                h = face[n][3]

                # 顔の切り取り
                face_cut = img[y:y + h, x:x + w]
                # リサイズ
                face_img = cv2.resize(face_cut, (img_size, img_size))

                # TFが使える形に加工
                face_img_d = face_img[None, :, :, np.newaxis]

                face_img_1 = tf.image.random_brightness(face_img_d, 0.15, seed=None)  # 明度ランダム変更
    
                # 保存
                result_img_name = 'data' + str(index) + '.jpg'
                cv2.imwrite(os.path.join(true_dir, result_img_name), face_img)  # オリジナル

                face_img_1 = np.array(face_img_1[0, :, :, 0])
                result_img_name = 'data_1_' + str(index) + '.jpg'
                cv2.imwrite(os.path.join(true_dir, result_img_name), face_img_1)  # 明度変更画像

                index += 1
        
                # 表示
                print("Processing success!!")

    print("___Successfully completed")


def main():
    # 動画->画像変換の有無
    video2img_flg = False
    if video2img_flg:
        # 動画が存在するフォルダ
        data_dir = os.path.abspath("face_data")

        # 動画->画像変換
        video2img(data_dir)
    
    # 画像フォルダ
    imgs_dir = os.path.abspath("img")
    # 保存先フォルダ
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_data")
    img_size = 96   # 画像サイズ(N x N)
    channel = 1     # 出力チャンネル数
    begin_index = 1070  # ファイル名開始インデックス
    # Haar-cascadeファイル
    haar_cascade = os.path.abspath("haar_cascade.xml")

    # 設定情報出力
    print("=== Setting information ===")
    print("# Image directory: {}".format(imgs_dir))
    print("# Output directory: {}".format(out_dir))
    print("# Images size: {}".format(img_size))
    print("# Channel: {}".format(channel))
    print("# Begin Index: {}".format(begin_index))
    print("# Haar-Cascade: {}".format(haar_cascade))
    print("===========================\n")

    # 顔領域切り取り
    face_crop(imgs_dir, out_dir, img_size, channel, begin_index, haar_cascade)


if __name__ == '__main__':
    main()
