#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀アシスタントセットアップスクリプト

このスクリプトは、麻雀アシスタントの初期設定を対話式で行います。
初めて使用する際に実行してください。
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess
import platform


def print_header(title):
    """ヘッダーを表示する"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_python_version():
    """Pythonのバージョンをチェックする"""
    print_header("Pythonバージョンの確認")
    
    major, minor = sys.version_info[:2]
    print(f"現在のPythonバージョン: {major}.{minor}")
    
    if major < 3 or (major == 3 and minor < 8):
        print("警告: Python 3.8以上が必要です。")
        print("最新バージョンをインストールしてください: https://www.python.org/downloads/")
        return False
    
    print("OK: Pythonバージョンの要件を満たしています。")
    return True


def check_dependencies():
    """必要なパッケージをチェックする"""
    print_header("依存パッケージの確認")
    
    required_packages = [
        "tensorflow", "opencv-python", "pygame", "numpy", 
        "pillow", "keyboard", "matplotlib", "scikit-learn"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} はインストール済みです。")
        except ImportError:
            print(f"✗ {package} が見つかりません。")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n以下のパッケージが不足しています:")
        for package in missing_packages:
            print(f"- {package}")
        
        install = input("\n不足しているパッケージをインストールしますか？(y/n): ")
        if install.lower() == 'y':
            print("\nパッケージをインストール中...")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("パッケージのインストールが完了しました。")
            return True
        else:
            print("\n依存パッケージのインストールをスキップします。")
            print("必要なパッケージをインストールしてから、もう一度試してください。")
            return False
    
    print("\nOK: すべての依存パッケージがインストール済みです。")
    return True


def create_directories():
    """必要なディレクトリを作成する"""
    print_header("ディレクトリ構造の作成")
    
    directories = [
        "dataset/tiles",
        "models/tile_recognition_model",
        "raw_images"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"ディレクトリを作成しました: {dir_path}")
        else:
            print(f"ディレクトリは既に存在します: {dir_path}")
    
    print("\nOK: ディレクトリ構造の確認が完了しました。")
    return True


def setup_game_capture():
    """ゲームキャプチャの設定"""
    print_header("ゲームキャプチャの設定")
    
    print("雀魂（じゃんたま/Mahjong Soul）の画面設定:")
    print("1. ブラウザでゲームを起動してください。")
    print("2. 認識精度を高めるため、以下の設定を推奨します:")
    print("   - 解像度: 1280 x 720 以上")
    print("   - ウィンドウモード: フルスクリーンではなくウィンドウモードを推奨")
    print("   - 牌のデザイン: 標準的なデザインを推奨")
    
    print("\nOK: ゲームキャプチャの設定情報を確認しました。")
    return True


def setup_image_dataset():
    """画像データセットの設定"""
    print_header("画像データセットの設定")
    
    print("牌認識の機械学習には、各牌タイプごとの画像データが必要です。")
    print("以下の方法で画像を収集できます:")
    print("1. スクリーンショットから牌の画像を切り抜く")
    print("2. 雀魂の牌のスクリーンショットを撮影")
    
    print("\n牌の画像を 'raw_images' フォルダに配置し、以下のコマンドで整理できます:")
    print("   python tools/organize_tile_images.py --interactive")
    
    print("\n整理された画像は 'dataset/tiles' フォルダに保存され、機械学習に使用されます。")
    
    sample_image = Path("assets/tiles") / "sample.png"
    if sample_image.exists():
        shutil.copy(sample_image, Path("raw_images") / "sample.png")
        print("\nサンプル画像を 'raw_images' フォルダにコピーしました。")
    
    print("\nOK: 画像データセット設定の確認が完了しました。")
    return True


def check_model_existence():
    """学習済みモデルの存在確認"""
    print_header("学習済みモデルの確認")
    
    model_path = Path("models/tile_recognition_model")
    model_files = list(model_path.glob("*.h5")) + list(model_path.glob("*.keras"))
    
    if model_files:
        print("学習済みモデルが見つかりました:")
        for model_file in model_files:
            print(f"- {model_file}")
        print("\nOK: 学習済みモデルが利用可能です。")
        return True
    else:
        print("学習済みモデルが見つかりません。")
        print("以下のコマンドで牌認識モデルをトレーニングできます:")
        print("   python tools/train_tile_recognition.py --data_dir=./dataset/tiles")
        print("\n注意: トレーニングには十分な画像データセットが必要です。")
        return False


def setup_shortcut():
    """起動ショートカットの設定"""
    print_header("起動ショートカットの設定")
    
    system = platform.system()
    
    if system == "Windows":
        # Windowsの場合はバッチファイルを作成
        batch_path = Path("start_assistant.bat")
        with open(batch_path, "w") as f:
            f.write("@echo off\n")
            f.write("echo 麻雀アシスタントを起動しています...\n")
            f.write("python main.py\n")
            f.write("pause\n")
        
        print(f"Windowsショートカットを作成しました: {batch_path}")
        print("このファイルをダブルクリックすると麻雀アシスタントが起動します。")
    
    elif system == "Darwin":  # macOS
        # macOSの場合はシェルスクリプトを作成
        script_path = Path("start_assistant.command")
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("cd \"$(dirname \"$0\")\"\n")
            f.write("echo 麻雀アシスタントを起動しています...\n")
            f.write("python main.py\n")
        
        # 実行権限を付与
        os.chmod(script_path, 0o755)
        
        print(f"macOSショートカットを作成しました: {script_path}")
        print("このファイルをダブルクリックすると麻雀アシスタントが起動します。")
    
    elif system == "Linux":
        # Linuxの場合はシェルスクリプトを作成
        script_path = Path("start_assistant.sh")
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo 麻雀アシスタントを起動しています...\n")
            f.write("python main.py\n")
        
        # 実行権限を付与
        os.chmod(script_path, 0o755)
        
        print(f"Linuxショートカットを作成しました: {script_path}")
        print("このファイルから麻雀アシスタントが起動します。")
    
    print("\nOK: 起動ショートカットの設定が完了しました。")
    return True


def main():
    """メイン関数"""
    print_header("麻雀アシスタントセットアップウィザード")
    
    print("このウィザードでは、麻雀アシスタントの初期設定を行います。")
    print("各ステップに従って設定を進めてください。")
    
    # Pythonバージョンの確認
    if not check_python_version():
        print("\n警告: Pythonのバージョンが要件を満たしていません。")
        print("セットアップを続行できますが、正常に動作しない可能性があります。")
        cont = input("続行しますか？(y/n): ")
        if cont.lower() != 'y':
            print("セットアップを終了します。")
            return
    
    # 依存パッケージの確認
    if not check_dependencies():
        print("\n警告: 依存パッケージの確認に問題があります。")
        cont = input("続行しますか？(y/n): ")
        if cont.lower() != 'y':
            print("セットアップを終了します。")
            return
    
    # ディレクトリ構造の作成
    create_directories()
    
    # ゲームキャプチャの設定
    setup_game_capture()
    
    # 画像データセットの設定
    setup_image_dataset()
    
    # 学習済みモデルの確認
    check_model_existence()
    
    # 起動ショートカットの設定
    setup_shortcut()
    
    print_header("セットアップ完了")
    
    print("麻雀アシスタントの初期設定が完了しました！")
    print("\n次のステップ:")
    print("1. 牌の画像を 'raw_images' フォルダに配置")
    print("2. 画像整理ツールを実行: python tools/organize_tile_images.py --interactive")
    print("3. 牌認識モデルをトレーニング: python tools/train_tile_recognition.py --data_dir=./dataset/tiles")
    print("4. アプリケーションを起動: python main.py")
    
    print("\nお疲れ様でした！")


if __name__ == "__main__":
    main()
