# 麻雀アシスタントツール

リアルタイム麻雀アシスタントツール - 雀魂向け画像認識と戦略提案システム

## プロジェクト概要

このプロジェクトは、雀魂（じゃんたま/Mahjong Soul）で遊ぶ際にリアルタイムでアシスタントを提供するツールです。画像認識技術を使用して画面から牌を読み取り、最適な戦略を提案します。

### 主な機能

- 画像認識による手牌、ドラ、河の自動検出
- 副露（鳴き）の検出と認識
- シャンテン数計算と有効牌の表示
- 捨て牌の推奨と危険牌の警告
- リーチ後の相手の待ち牌予測
- 雀魂のUI/UXに合わせたデザイン

## システム構成

プロジェクトは以下の主要コンポーネントから構成されています：

1. **画像認識モジュール**：画面をキャプチャし、牌を認識
   - 牌認識システム
   - 副露認識システム
2. **麻雀ロジックエンジン**：シャンテン数計算、最適戦略の決定
3. **UI表示システム**：結果の視覚化と操作インターフェース

## インストール方法

### 前提条件

- Python 3.8以上
- 必要なパッケージ：TensorFlow, OpenCV, PyGame, NumPy, Pillow

### インストール手順

```bash
# リポジトリのクローン
git clone https://github.com/jokerjp1234/mahjang-assistant-test.git
cd mahjang-assistant-test

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 実行
python main.py
```

## 使用方法

1. 雀魂をブラウザまたはクライアントで起動
2. 本アシスタントツールを起動
3. 画面領域設定ウィザードに従って認識領域を設定
4. ホットキー（Ctrl+Alt+H）でアシスタントの表示/非表示を切り替え

## ファイル構成

- `main.py`: メインプログラム
- `recognizer/`: 画像認識関連モジュール
  - `tile_recognizer.py`: 基本牌認識システム
  - `meld_recognizer.py`: 副露（鳴き）認識システム
  - `enhanced_recognizer.py`: 副露対応拡張牌認識システム
  - `screen_capture.py`: 画面キャプチャ機能
- `engine/`: 麻雀ロジックエンジン
  - `mahjong_engine.py`: 基本麻雀ロジック
  - `shanten.py`: シャンテン数計算
  - `score_calculator.py`: 点数計算
- `ui/`: ユーザーインターフェース
  - `assistant_ui.py`: メイン表示UI
  - `setup_wizard.py`: 初期設定ウィザード
- `assets/`: 画像・サウンドなどのリソース
- `models/`: 学習済みモデル
- `tools/`: 開発・トレーニング用ツール
  - `organize_tile_images.py`: 画像整理ツール
  - `train_tile_recognition.py`: モデルトレーニングツール
  - `export_model.py`: モデルエクスポートツール
- `docs/`: ドキュメント
  - `meld_recognition.md`: 副露認識機能の説明

## 機械学習モデルのトレーニング

牌認識の精度を向上させるためのツールが `tools/` ディレクトリに用意されています。

1. 撮影した牌の画像を整理する
   ```bash
   python tools/organize_tile_images.py --input_dir=./raw_images --output_dir=./dataset/tiles --interactive
   ```

2. 整理した画像データでモデルをトレーニングする
   ```bash
   python tools/train_tile_recognition.py --data_dir=./dataset/tiles --epochs=50
   ```

3. トレーニング済みモデルをエクスポートする
   ```bash
   python tools/export_model.py --model_path=models/tile_recognition_model/best_model.h5 --output_dir=models/tile_recognition_model
   ```

詳しくは `tools/README.md` を参照してください。

## 副露（鳴き）認識機能

このツールは牌の副露（チー、ポン、カン）も認識できます。副露があると手牌の位置やツモ牌の位置が変わりますが、自動的に調整して認識します。

詳しくは `docs/meld_recognition.md` を参照してください。

## 今後の開発予定

- [x] 副露（鳴き）認識機能の追加
- [ ] 多様な画面解像度への対応
- [ ] より高精度な牌認識モデルの開発
- [ ] 戦略エンジンの強化
- [ ] 統計機能の追加

## ライセンス

MIT

## 注意事項

このプロジェクトは個人の学習・トレーニング目的で作成されています。実際のゲームでの使用はサービスの利用規約に違反する可能性があります。
