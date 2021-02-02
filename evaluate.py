import numpy as np

import os
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # TFメッセージ非表示

import tensorflow as tf
import tensorflow.keras.layers as kl
import cv2

def main():

    evadir = os.path.abspath("./face_data") # 評価データフォルダ
    param = os.path.abspath("converted_model.tflite")   # モデル

    # モデル読み込み
    interpreter = tf.lite.Interpreter(model_path=param)
    interpreter.allocate_tensors()

    # 入力/出力のtensor取得
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    t = 0
    p = 0
    n = 0
    tt = 0
    tp = 0
    tn = 0
    label = 0

    # 評価
    for eva_dir in os.listdir(evadir): 
        
        print("Evaluation Dir: {}".format(eva_dir))

        eva_imgdir = os.path.join(evadir, eva_dir)
        eva_imgs = os.listdir(eva_imgdir)
    
        # JPEG形式の画像のみ評価
        for img_name in [f for f in eva_imgs if ('jpg' in f)]:
            t += 1

            img_path = os.path.join(eva_imgdir, img_name)

            # データ読み込み・加工
            img = cv2.imread(img_path)
            img = np.asarray(img)
            img = img / 255
            img = img[np.newaxis, :, :]
            img = tf.convert_to_tensor(img, np.float32)

            # 推論
            interpreter.set_tensor(input_details[0]['index'], img)
            interpreter.invoke()
            y = interpreter.get_tensor(output_details[0]['index'])

            a = np.argmax(y)
            if label != a:
                n += 1  # 不正解
            else:
                p += 1  # 正解

        # 1クラスの予測精度表示
        print("Total: {0} Positive: {1} Negative: {2}".format(t, p, n))
        par = (p / t) * 100
        print("acc_par: {:.2f}\n".format(par))

        tt += t
        tp += p
        tn += n

        label += 1
        t = 0
        n = 0
        p = 0
        par = 0
    
    # 全体の予測精度表示
    print("\nTotal: {0} Positive: {1} Negative: {2}".format(tt, tp, tn))
    tpar = (tp / tt) * 100
    print("acc_par: {:.2f}\n".format(tpar))
    
if __name__ == "__main__":
    main()