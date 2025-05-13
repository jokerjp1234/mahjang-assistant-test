#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀牌画像整理ツール

このスクリプトは、撮影した麻雀牌の画像を整理し、各牌タイプごとのフォルダに
分類するためのツールです。

使用方法:
    python organize_tile_images.py --input_dir=./raw_images --output_dir=./dataset/tiles

オプション:
    --input_dir: 撮影した麻雀牌画像が格納されているディレクトリ
    --output_dir: 整理された画像を保存するディレクトリ
    --resize: リサイズする場合のサイズ（例: 64x64）
    --interactive: 対話モードで各画像を確認しながら分類
"""

import os
import sys
import argparse
import shutil
import cv2
import numpy as np
from pathlib import Path
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
    parser = argparse.ArgumentParser(description='麻雀牌画像整理ツール')
    parser.add_argument('--input_dir', type=str, default='./raw_images',
                        help='撮影した麻雀牌画像が格納されているディレクトリ（デフォルト: ./raw_images）')
    parser.add_argument('--output_dir', type=str, default='./dataset/tiles',
                        help='整理された画像を保存するディレクトリ（デフォルト: ./dataset/tiles）')
    parser.add_argument('--resize', type=str, default='64x64',
                        help='リサイズするサイズ（例: 64x64）（デフォルト: 64x64）')
    parser.add_argument('--interactive', action='store_true',
                        help='対話モードで各画像を確認しながら分類')
    parser.add_argument('--auto_create', action='store_true',
                        help='入力ディレクトリが存在しない場合に自動作成する')
    
    # 引数をパースし、ヘルプが必要かチェック
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    return parser.parse_args()


def resize_image(image, size_str):
    """画像をリサイズする"""
    width, height = map(int, size_str.split('x'))
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def show_image_and_get_type(image, window_name="Select Tile Type"):
    """画像を表示し、ユーザーから牌の種類を入力してもらう"""
    cv2.imshow(window_name, image)
    cv2.waitKey(100)  # 少し待機して確実に表示されるようにする
    
    print("\n利用可能な牌のタイプ:")
    for idx, (tile_id, tile_name) in enumerate(TILE_TYPES.items()):
        print(f"{tile_id}: {tile_name}", end='\t')
        if (idx + 1) % 5 == 0:
            print()
    print("\n")
    
    while True:
        tile_type = input("この画像の牌の種類を選択してください（IDを入力、xでスキップ、qで終了）: ")
        if tile_type == 'x':
            return None
        if tile_type == 'q':
            print("処理を中断します。")
            sys.exit(0)
        if tile_type in TILE_TYPES:
            return tile_type
        print("無効な牌タイプです。もう一度入力してください。")


def main():
    """メイン関数"""
    args = parse_arguments()
    
    # 入力ディレクトリの存在確認
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        if args.auto_create:
            print(f"入力ディレクトリ '{input_dir}' が存在しないため、作成します。")
            input_dir.mkdir(parents=True, exist_ok=True)
            print(f"'{input_dir}' にサンプル画像を配置してください。")
            print("プログラムを終了します。プログラムを再実行してください。")
            sys.exit(0)
        else:
            print(f"エラー: 入力ディレクトリ '{input_dir}' が存在しません。")
            print("以下のオプションがあります:")
            print("1. --auto_create オプションを使用して自動的に作成")
            print("2. 手動で入力ディレクトリを作成")
            sys.exit(1)
    
    # 出力ディレクトリの作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 各牌タイプのディレクトリを作成
    for tile_id in TILE_TYPES.keys():
        tile_dir = output_dir / tile_id
        tile_dir.mkdir(exist_ok=True)
    
    # 未分類画像の保存先
    unclassified_dir = output_dir / 'unclassified'
    unclassified_dir.mkdir(exist_ok=True)
    
    # 対応する画像拡張子
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # 画像ファイルの収集
    image_files = []
    for ext in valid_extensions:
        image_files.extend(list(input_dir.glob(f'*{ext}')))
        # 大文字の拡張子も対応
        image_files.extend(list(input_dir.glob(f'*{ext.upper()}')))
    
    if not image_files:
        print(f"警告: 入力ディレクトリ '{input_dir}' に画像ファイルが見つかりません。")
        print(f"対応している拡張子: {', '.join(valid_extensions)}")
        sys.exit(1)
    
    print(f"合計 {len(image_files)} 個の画像ファイルが見つかりました。")
    
    # リサイズサイズの解析
    resize_dimensions = args.resize
    
    # 対話モードで画像を分類
    if args.interactive:
        cv2.namedWindow("Select Tile Type", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Select Tile Type", 400, 400)  # ウィンドウサイズの調整
        
        print("\n対話モードを開始します。各画像を表示し、牌の種類を選択していただきます。")
        print("- 各牌タイプのID（例: m1, p5, zeast）を入力して選択")
        print("- 'x' を入力するとその画像をスキップ（未分類として保存）")
        print("- 'q' を入力するといつでも終了できます")
        
        for idx, img_path in enumerate(image_files):
            print(f"\n画像 {idx+1}/{len(image_files)}: {img_path.name}")
            
            # 画像の読み込み
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"警告: 画像 '{img_path}' を読み込めませんでした。スキップします。")
                continue
            
            # 画像の表示と牌の種類の取得
            tile_type = show_image_and_get_type(img)
            
            if tile_type:
                # リサイズ
                img_resized = resize_image(img, resize_dimensions)
                
                # ファイル名の生成（タイムスタンプを含める）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                output_filename = f"{tile_type}_{timestamp}{img_path.suffix}"
                output_path = output_dir / tile_type / output_filename
                
                # 画像の保存
                cv2.imwrite(str(output_path), img_resized)
                print(f"保存しました: {output_path}")
            else:
                # 未分類として保存
                dest_path = unclassified_dir / img_path.name
                shutil.copy(img_path, dest_path)
                print(f"未分類として保存しました: {dest_path}")
        
        cv2.destroyAllWindows()
    
    else:
        # 非対話モードの場合：ファイル名からタイプを推測するなどの自動処理
        print("非対話モード: ファイル名からの自動分類を行います。")
        print("ファイル名の先頭に牌タイプのIDを付けてください（例: m1_image1.jpg）")
        
        classified_count = 0
        for img_path in image_files:
            filename = img_path.stem.lower()
            found_type = None
            
            # ファイル名から牌タイプを推測
            for tile_id in TILE_TYPES.keys():
                if filename.startswith(tile_id):
                    found_type = tile_id
                    break
            
            if found_type:
                # 画像の読み込みとリサイズ
                img = cv2.imread(str(img_path))
                if img is None:
                    print(f"警告: 画像 '{img_path}' を読み込めませんでした。スキップします。")
                    continue
                
                img_resized = resize_image(img, resize_dimensions)
                
                # ファイル名の生成
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                output_filename = f"{found_type}_{timestamp}{img_path.suffix}"
                output_path = output_dir / found_type / output_filename
                
                # 画像の保存
                cv2.imwrite(str(output_path), img_resized)
                classified_count += 1
            else:
                # 未分類として保存
                dest_path = unclassified_dir / img_path.name
                shutil.copy(img_path, dest_path)
        
        print(f"合計 {classified_count} 個の画像を分類しました。")
        print(f"未分類の画像は {len(image_files) - classified_count} 個です。")
    
    print("\n画像の整理が完了しました！")
    print(f"分類された画像は {output_dir} に保存されました。")
    print(f"未分類の画像は {unclassified_dir} にあります。")
    
    # クラスごとの画像数を表示
    print("\n各牌タイプの画像数:")
    for tile_id in TILE_TYPES.keys():
        tile_dir = output_dir / tile_id
        img_count = len(list(tile_dir.glob('*.jpg'))) + len(list(tile_dir.glob('*.png')))
        if img_count > 0:
            print(f"{tile_id} ({TILE_TYPES[tile_id]}): {img_count}枚")
    
    # 学習に十分なデータがあるか確認
    min_count = 10  # 最小推奨枚数
    low_count_classes = []
    
    for tile_id in TILE_TYPES.keys():
        tile_dir = output_dir / tile_id
        img_count = len(list(tile_dir.glob('*.jpg'))) + len(list(tile_dir.glob('*.png')))
        if img_count < min_count:
            low_count_classes.append((tile_id, img_count))
    
    if low_count_classes:
        print("\n警告: 以下の牌タイプは学習に十分な画像数がありません（推奨: 各タイプ10枚以上）")
        for tile_id, count in low_count_classes:
            print(f"{tile_id} ({TILE_TYPES[tile_id]}): {count}枚")
        
        print("\n学習の精度を高めるために、これらの牌タイプの画像を追加してください。")
    else:
        print("\n全ての牌タイプに十分な画像数があります。このデータセットで学習を開始できます。")


if __name__ == "__main__":
    main()
