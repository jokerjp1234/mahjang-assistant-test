#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀牌認識モデルのエクスポートツール

このスクリプトは、トレーニング済みの麻雀牌認識モデルを
アプリケーションで使用するためにエクスポートします。

使用方法:
    python export_model.py --model_path=models/tile_recognition_model/best_model.keras --output_dir=models/tile_recognition_model

オプション:
    --model_path: トレーニング済みモデルのパス
    --output_dir: エクスポートしたモデルの出力先ディレクトリ
    --image_size: 画像サイズ（例: 64x64）
"""

import os
import sys
import argparse
import numpy as np
import tensorflow as tf
from pathlib import Path
from tensorflow.keras.models import load_model
import json
import shutil


def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description='麻雀牌認識モデルエクスポートツール')
    parser.add_argument('--model_path', type=str, required=True,
                        help='トレーニング済みモデルのパス')
    parser.add_argument('--output_dir', type=str, default='models/exported_model',
                        help='エクスポートしたモデルの出力先ディレクトリ')
    parser.add_argument('--image_size', type=str, default='64x64',
                        help='画像サイズ（例: 64x64）')
    return parser.parse_args()


def load_class_mapping(model_dir):
    """クラスマッピングファイルを読み込む"""
    model_dir = Path(model_dir)
    mapping_file = model_dir / 'class_mapping.txt'
    
    if not mapping_file.exists():
        print(f"警告: クラスマッピングファイル '{mapping_file}' が見つかりません。")
        return None
    
    class_mapping = {}
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    idx = int(parts[0])
                    tile_id = parts[1]
                    class_mapping[idx] = tile_id
    except Exception as e:
        print(f"クラスマッピングファイルの読み込み中にエラーが発生しました: {e}")
        return None
    
    return class_mapping


def create_metadata_file(output_dir, class_mapping, image_size):
    """メタデータファイルを作成する"""
    if class_mapping is None:
        return
    
    output_dir = Path(output_dir)
    metadata = {
        "input_image_size": image_size,
        "class_mapping": class_mapping
    }
    
    try:
        with open(output_dir / 'model_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"メタデータファイルを保存しました: {output_dir / 'model_metadata.json'}")
    except Exception as e:
        print(f"メタデータファイルの作成中にエラーが発生しました: {e}")


def export_to_tflite(model, output_dir, optimize=True):
    """モデルをTensorFlow Lite形式にエクスポートする"""
    output_dir = Path(output_dir)
    try:
        # TFLiteコンバーターの作成
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # 最適化の設定（オプション）
        if optimize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # 変換の実行
        tflite_model = converter.convert()
        
        # ファイルに保存
        tflite_file = output_dir / 'model.tflite'
        with open(tflite_file, 'wb') as f:
            f.write(tflite_model)
        
        print(f"TensorFlow Liteモデルを保存しました: {tflite_file}")
        return True
    except Exception as e:
        print(f"TensorFlow Liteへの変換中にエラーが発生しました: {e}")
        return False


def save_example_code(output_dir, class_mapping, image_size):
    """モデル使用のためのサンプルコードを保存する"""
    output_dir = Path(output_dir)
    
    # Python用のサンプルコード
    python_code = f"""
# 麻雀牌認識モデルの使用例
import cv2
import numpy as np
import tensorflow as tf

# モデルの読み込み
model_path = "{output_dir.name}/model.tflite"
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# 入出力テンソルの取得
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# クラスマッピング
class_mapping = {class_mapping}

def recognize_tile(image_path):
    # 画像の読み込みとリサイズ
    img = cv2.imread(image_path)
    img = cv2.resize(img, ({image_size.replace('x', ', ')}))
    
    # 前処理
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    
    # 推論
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    
    # 結果の処理
    predicted_class = np.argmax(output[0])
    confidence = output[0][predicted_class]
    
    tile_id = class_mapping.get(str(predicted_class), "unknown")
    return tile_id, confidence

# 使用例
tile_id, confidence = recognize_tile("path/to/tile_image.jpg")
print(f"認識結果: {tile_id}, 確信度: {confidence:.2f}")
"""
    
    try:
        with open(output_dir / 'example_usage.py', 'w', encoding='utf-8') as f:
            f.write(python_code)
        print(f"サンプルコードを保存しました: {output_dir / 'example_usage.py'}")
    except Exception as e:
        print(f"サンプルコードの作成中にエラーが発生しました: {e}")


def main():
    """メイン関数"""
    args = parse_arguments()
    
    # モデルパスの確認
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"エラー: モデルファイル '{model_path}' が存在しません。")
        sys.exit(1)
    
    # モデルディレクトリの取得
    model_dir = model_path.parent
    
    # 出力ディレクトリの作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # モデルの読み込み
    print(f"モデルを読み込んでいます: {model_path}")
    try:
        model = load_model(model_path)
        print("モデルの読み込みに成功しました。")
    except Exception as e:
        print(f"モデルの読み込み中にエラーが発生しました: {e}")
        sys.exit(1)
    
    # モデルの概要表示
    model.summary()
    
    # クラスマッピングの読み込み
    class_mapping = load_class_mapping(model_dir)
    
    # クラスマッピングファイルのコピー（存在する場合）
    mapping_file = model_dir / 'class_mapping.txt'
    if mapping_file.exists():
        shutil.copy(mapping_file, output_dir / 'class_mapping.txt')
        print(f"クラスマッピングファイルをコピーしました: {output_dir / 'class_mapping.txt'}")
    
    # モデルのエクスポート
    # 1. SavedModel形式
    print("\nSavedModel形式でエクスポートしています...")
    saved_model_dir = output_dir / 'saved_model'
    try:
        # 最新のTensorFlowではsave_modelを使用
        tf.keras.models.save_model(model, saved_model_dir)
        print(f"SavedModelを保存しました: {saved_model_dir}")
    except Exception as e:
        print(f"SavedModel形式でのエクスポート中にエラーが発生しました: {e}")
    
    # 2. Keras形式
    print("\nKeras形式でエクスポートしています...")
    keras_path = output_dir / 'model.keras'
    try:
        model.save(keras_path)
        print(f"Kerasモデルを保存しました: {keras_path}")
    except Exception as e:
        print(f"Keras形式でのエクスポート中にエラーが発生しました: {e}")
    
    # 3. TensorFlow Lite形式
    print("\nTensorFlow Lite形式でエクスポートしています...")
    export_to_tflite(model, output_dir)
    
    # メタデータファイルの作成
    create_metadata_file(output_dir, class_mapping, args.image_size)
    
    # サンプルコードの保存
    save_example_code(output_dir, class_mapping, args.image_size)
    
    print("\nモデルのエクスポートが完了しました！")


if __name__ == "__main__":
    main()
