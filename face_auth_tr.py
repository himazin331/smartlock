import cv2

import os
import sys

import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # TFメッセージ非表示

import tensorflow as tf
import tensorflow.keras.layers as kl

import matplotlib.pyplot as plt

class Trainer():
    def __init__(self, img_size=96):
        # 画像サイズ
        img_shape = (img_size, img_size, 3)

        # MobileNetV2
        base_model = tf.keras.applications.MobileNetV2(input_shape=img_shape,
                                                    include_top=False,
                                                    weights='imagenet')
        base_model.trainable = False
        global_average_layer = kl.GlobalAveragePooling2D()
        prediction_layer = kl.Dense(2)

        # 訓練モデル
        self.model = tf.keras.Sequential([
            base_model,
            global_average_layer,
            prediction_layer
        ])

        self.model.compile(optimizer=tf.keras.optimizers.Adam(),
                            loss=tf.keras.losses.BinaryCrossentropy(),
                            metrics=['accuracy'])

    # 訓練
    def train(self, dataset, batch_size, epoch, out_dir):
        train_img, train_lab = dataset

        his = self.model.fit(train_img, train_lab, batch_size=batch_size, epochs=epoch)

        # tflite形式で保存
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        tflite_model = converter.convert()
        open("./converted_model.tflite", "wb").write(tflite_model)

        return his

# データセット作成
def create_dataset(data_dir, channel):
    
    print("\n___Creating a dataset...")
    
    cnt = 0
    cnt_t = 0
    prc = ['/', '-', '\\', '|']
    
    # 画像データの個数
    for c in os.listdir(data_dir):
        d = os.path.join(data_dir, c)
        print("Number of image in a directory \"{}\": {}".format(c, len(os.listdir(d))))
        
    train_img = [] # 画像データ(テンソル)
    train_lab = [] # ラベル
    label = 0
    
    for c in os.listdir(data_dir):

        print("\nclass: {},   class id: {}".format(c, label))   # 画像フォルダ名とクラスIDの出力
        
        d = os.path.join(data_dir, c)                # フォルダ名と画像フォルダ名の結合
        imgs = os.listdir(d)
        
        # JPEG形式の画像データだけを読込
        for i in [f for f in imgs if ('jpg'or'JPG' in f)]:     
            # キャッシュファイルをスルー
            if i == 'Thumbs.db':
                continue

            img = tf.io.read_file(os.path.join(d, i))       # 画像フォルダパスと画像パスを結合後、読込
            img = tf.image.decode_image(img, channels=channel)    # Tensorflowフォーマットに従ってデコード
            img /= 255     # 正規化

            train_img.append(img)       # 画像データ(テンソル)追加
            train_lab.append(label)     # ラベル追加
            
            cnt += 1
            cnt_t += 1
            print("\r   Loading a images and labels...{}    ({} / {})".format(prc[cnt_t%4], cnt, len(os.listdir(d))), end='')
        print("\r   Loading a images and labels...Done    ({} / {})".format(cnt, len(os.listdir(d))), end='')
        
        label += 1
        cnt = 0
    train_img = tf.convert_to_tensor(train_img, np.float32) # 画像データセット
    train_lab = tf.convert_to_tensor(train_lab, np.int64)   # ラベルデータセット
    print("\n___Successfully completed\n")

    return train_img, train_lab

def graph_output(history):
    # 予測精度グラフ
    plt.plot(history.history['accuracy'])
    plt.title('Model accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train'], loc='upper left')
    plt.show()  

    # 損失値グラフ
    plt.plot(history.history['loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train'], loc='upper left')
    plt.show()

def main():
    # 訓練データフォルダ
    train_dir = os.path.abspath("train_data")
    # 保存先フォルダ
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result")
    os.makedirs(out_dir, exist_ok=True) # フォルダ作成
    img_size = 96       # 画像サイズ(N x N)
    channel = 3         # 出力チャンネル数
    batch_size = 32     # ミニバッチサイズ
    epoch = 8          # 訓練回数

    # 設定情報出力
    print("=== Setting information ===")
    print("# Output directory: {}".format(out_dir))
    print("# Train directory: {}".format(train_dir))
    print("# Images size: {}".format(img_size))
    print("# Channel: {}".format(channel))
    print("# Minibatch-size: {}".format(batch_size))
    print("# Epoch: {}".format(epoch))
    print("===========================\n")

    # データセット作成
    dataset = create_dataset(train_dir, channel)

    # 学習
    trainer = Trainer(img_size)
    his = trainer.train(dataset, batch_size, epoch, out_dir)

    # 精度, 損失値グラフ出力
    graph_output(his)
if __name__ == '__main__':
    main()