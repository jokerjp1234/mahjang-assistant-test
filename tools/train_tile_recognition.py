#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀牌認識のための機械学習モデルトレーニングスクリプト

このスクリプトは、整理された麻雀牌の画像データセットを使用して
牌認識のためのCNNモデルをトレーニングします。

使用方法:
    python train_tile_recognition.py --data_dir=./dataset/tiles --epochs=50

オプション:
    --data_dir: 牌画像データセットのディレクトリ（各牌タイプごとにサブディレクトリが必要）
    --output_dir: トレーニング済みモデルの出力先ディレクトリ
    --epochs: トレーニングのエポック数
    --batch_size: バッチサイズ
    --validation_split: 検証データの割合
    --learning_rate: 学習率
    --image_size: 画像サイズ（例: 64x64）
"""

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
from datetime import datetime


# 麻雀牌の種類を定義
TILE_TYPES = {
    # 萬子 (m1-m9)
    'm1': '一萬', 'm2': '二萬', 'm3': '三萬', 'm4': '四萬', 'm5': '五萬',
    'm6': '六萬', 'm7': '七萬', 'm8': '八萬', 'm9': '九萬',
    
    # 筒子 (p1-p9)
    'p1': '一筒', 'p2': '二筒', 'p3': '三筒', 'p4': '四筒', 'p5': '五筒',
    'p6': '六筒', 'p7': '七筒', 'p8': '八筒', 'p9': '九筒',
    
    # 索子 (s1-s9)
    's1': '一索', 's2': '二索', 's3': '三索', 's4': '四索', 's5': '五索',
    's6': '六索', 's7': '七索', 's8': '八索', 's9': '九索',
    
    # 字牌 (風牌と三元牌)
    'zeast': '東', 'zsouth': '南', 'zwest': '西', 'znorth': '北',
    'zwhite': '白', 'zgreen': '發', 'zred': '中'
}


def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description='麻雀牌認識モデルトレーニングツール')
    parser.add_argument('--data_dir', type=str, required=True,
                        help='牌画像データセットのディレクトリ')
    parser.add_argument('--output_dir', type=str, default='models/tile_recognition_model',
                        help='トレーニング済みモデルの出力先ディレクトリ')
    parser.add_argument('--epochs', type=int, default=50,
                        help='トレーニングのエポック数')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='バッチサイズ')
    parser.add_argument('--validation_split', type=float, default=0.2,
                        help='検証データの割合')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                        help='学習率')
    parser.add_argument('--image_size', type=str, default='64x64',
                        help='画像サイズ（例: 64x64）')
    return parser.parse_args()


def check_dataset(data_dir):
    """データセットの構造を確認し、各クラスの画像数をカウントする"""
    data_dir = Path(data_dir)
    
    if not data_dir.exists():
        print(f"エラー: データディレクトリ '{data_dir}' が存在しません。")
        sys.exit(1)
    
    class_counts = {}
    total_images = 0
    
    # 各クラスディレクトリの存在確認
    for tile_id in TILE_TYPES.keys():
        class_dir = data_dir / tile_id
        if not class_dir.exists():
            print(f"警告: クラスディレクトリ '{class_dir}' が見つかりません。")
            class_counts[tile_id] = 0
            continue
        
        # 画像数のカウント
        image_count = len(list(class_dir.glob('*.jpg'))) + len(list(class_dir.glob('*.png')))
        class_counts[tile_id] = image_count
        total_images += image_count
    
    # クラスごとの画像数のレポート
    print("\nデータセット統計:")
    print(f"合計クラス数: {len(TILE_TYPES)}")
    print(f"合計画像数: {total_images}")
    print("\nクラスごとの画像数:")
    
    for tile_id, count in class_counts.items():
        print(f"{tile_id} ({TILE_TYPES[tile_id]}): {count}枚")
    
    # 画像数が少ないクラスの警告
    min_recommended = 50
    low_count_classes = [(tile_id, count) for tile_id, count in class_counts.items() if count < min_recommended]
    
    if low_count_classes:
        print("\n警告: 以下のクラスは推奨最小画像数より少ないです。モデルの精度に影響する可能性があります。")
        for tile_id, count in low_count_classes:
            print(f"{tile_id} ({TILE_TYPES[tile_id]}): {count}枚 (推奨: {min_recommended}枚以上)")
    
    return total_images > 0


def create_model(input_shape, num_classes):
    """麻雀牌認識用のCNNモデルを構築する"""
    model = models.Sequential([
        # 入力層
        layers.Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=input_shape),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # 畳み込み層 1
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # 畳み込み層 2
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # 畳み込み層 3
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        
        # 平坦化層
        layers.Flatten(),
        
        # 全結合層
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model


def plot_training_history(history, output_dir):
    """トレーニング履歴をプロットしてファイルに保存する"""
    # 精度のプロット
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('Model Accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='lower right')
    
    # 損失のプロット
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    
    # 保存
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'training_history.png'))
    plt.close()


def save_model_safely(model, output_dir):
    """さまざまな形式でモデルを安全に保存する"""
    # 出力ディレクトリが存在することを確認
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Keras形式 (.keras)
    try:
        keras_path = output_dir / 'model.keras'
        model.save(keras_path)
        print(f"Kerasモデルを保存しました: {keras_path}")
    except Exception as e:
        print(f"Keras形式での保存に失敗しました: {e}")
        try:
            # 代替：.h5形式
            h5_path = output_dir / 'model.h5'
            model.save(h5_path)
            print(f"H5モデルを保存しました: {h5_path}")
        except Exception as e2:
            print(f"H5形式での保存にも失敗しました: {e2}")
    
    # 2. SavedModel形式
    try:
        saved_model_dir = output_dir / 'saved_model'
        tf.saved_model.save(model, str(saved_model_dir))
        print(f"SavedModelを保存しました: {saved_model_dir}")
    except Exception as e:
        print(f"SavedModel形式での保存に失敗しました: {e}")
        try:
            # 代替：exportメソッド（TF 2.13以降）
            export_dir = output_dir / 'exported_model'
            if hasattr(model, 'export'):
                model.export(export_dir)
                print(f"Exportされたモデルを保存しました: {export_dir}")
            else:
                print("モデルにexportメソッドがありません。TensorFlow 2.13以降が必要です。")
        except Exception as e2:
            print(f"Export形式での保存にも失敗しました: {e2}")
    
    # 3. TFLite形式
    try:
        # TFLiteコンバーターの作成
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        
        # TFLiteモデルを保存
        tflite_path = output_dir / 'model.tflite'
        with open(tflite_path, 'wb') as f:
            f.write(tflite_model)
        
        print(f"TensorFlow Liteモデルを保存しました: {tflite_path}")
    except Exception as e:
        print(f"TFLite形式での保存に失敗しました: {e}")


def main():
    """メイン関数"""
    # 引数の解析
    args = parse_arguments()
    
    # データセットの確認
    if not check_dataset(args.data_dir):
        print("エラー: 有効なデータセットが見つかりません。")
        sys.exit(1)
    
    # 画像サイズの解析
    width, height = map(int, args.image_size.split('x'))
    input_shape = (height, width, 3)  # RGB画像
    
    # 出力ディレクトリの作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # データ拡張の設定
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=10,
        width_shift_range=0.1,
        height_shift_range=0.1,
        brightness_range=[0.9, 1.1],
        zoom_range=0.1,
        channel_shift_range=0.1,
        fill_mode='nearest',
        validation_split=args.validation_split
    )
    
    # トレーニングデータの生成
    train_generator = train_datagen.flow_from_directory(
        args.data_dir,
        target_size=(height, width),
        batch_size=args.batch_size,
        color_mode='rgb',
        class_mode='categorical',
        subset='training',
        shuffle=True
    )
    
    # 検証データの生成
    validation_generator = train_datagen.flow_from_directory(
        args.data_dir,
        target_size=(height, width),
        batch_size=args.batch_size,
        color_mode='rgb',
        class_mode='categorical',
        subset='validation',
        shuffle=False
    )
    
    # クラス数の取得
    num_classes = len(train_generator.class_indices)
    
    # クラスインデックスと牌IDのマッピングを保存
    class_indices = train_generator.class_indices
    class_mapping = {v: k for k, v in class_indices.items()}
    
    with open(output_dir / 'class_mapping.txt', 'w', encoding='utf-8') as f:
        for idx, tile_id in class_mapping.items():
            tile_name = TILE_TYPES.get(tile_id, tile_id)
            f.write(f"{idx}\t{tile_id}\t{tile_name}\n")
    
    print(f"\nクラスマッピングを保存しました: {output_dir / 'class_mapping.txt'}")
    
    # モデルの構築
    model = create_model(input_shape, num_classes)
    
    # モデルの概要表示
    model.summary()
    
    # オプティマイザーの設定
    optimizer = optimizers.Adam(learning_rate=args.learning_rate)
    
    # モデルのコンパイル
    model.compile(
        optimizer=optimizer,
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # コールバックの設定
    callbacks = [
        ModelCheckpoint(
            filepath=output_dir / 'best_model.h5',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        ),
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        ),
        TensorBoard(
            log_dir=output_dir / 'logs' / datetime.now().strftime("%Y%m%d-%H%M%S"),
            histogram_freq=1
        )
    ]
    
    # トレーニングの実行
    print("\nモデルトレーニングを開始します...")
    history = model.fit(
        train_generator,
        epochs=args.epochs,
        validation_data=validation_generator,
        callbacks=callbacks,
        verbose=1
    )
    
    # トレーニング履歴のプロット
    plot_training_history(history, output_dir)
    
    # モデルの安全な保存
    print("\nモデルを保存しています...")
    save_model_safely(model, output_dir)
    
    print(f"\nトレーニングが完了しました！")
    print(f"モデルは {output_dir} に保存されました。")
    
    # モデル評価の表示
    print("\n最終評価結果:")
    
    # 検証データでの評価
    val_loss, val_accuracy = model.evaluate(validation_generator)
    print(f"検証データの精度: {val_accuracy:.4f}")
    print(f"検証データの損失: {val_loss:.4f}")
    
    # 混同行列の生成と保存（オプション）
    try:
        print("\n混同行列の生成中...")
        # 予測
        predictions = model.predict(validation_generator)
        y_pred = np.argmax(predictions, axis=1)
        
        # 実際のラベル
        validation_generator.reset()
        y_true = validation_generator.classes
        
        # クラス名の取得
        class_names = [class_mapping[i] for i in range(num_classes)]
        
        # 混同行列の計算
        from sklearn.metrics import confusion_matrix, classification_report
        cm = confusion_matrix(y_true, y_pred)
        
        # 混同行列のプロット
        plt.figure(figsize=(12, 10))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title('Confusion Matrix')
        plt.colorbar()
        tick_marks = np.arange(len(class_names))
        plt.xticks(tick_marks, class_names, rotation=90)
        plt.yticks(tick_marks, class_names)
        
        # 値の表示
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(j, i, format(cm[i, j], 'd'),
                         horizontalalignment="center",
                         color="white" if cm[i, j] > thresh else "black")
        
        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
        plt.savefig(output_dir / 'confusion_matrix.png')
        plt.close()
        
        # 分類レポートの生成と保存
        report = classification_report(y_true, y_pred, target_names=class_names)
        print("\n分類レポート:")
        print(report)
        
        with open(output_dir / 'classification_report.txt', 'w') as f:
            f.write(report)
        
    except Exception as e:
        print(f"混同行列の生成中にエラーが発生しました: {e}")


def predict_sample_images(model, data_dir, output_dir, image_size):
    """サンプル画像で予測を行い、結果を視覚化する"""
    # この機能は必要に応じて実装
    pass


if __name__ == "__main__":
    main()
