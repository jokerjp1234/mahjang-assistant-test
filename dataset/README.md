# 学習用データセットディレクトリ

このディレクトリには、麻雀牌認識モデルの学習に使用するデータセットが格納されます。

## ディレクトリ構造

- `tiles/` - 麻雀牌画像のデータセット
  - `m1/`, `m2/`, ... - 各牌タイプごとのフォルダ（整理後に作成）

## データセットの準備方法

データセットは以下の手順で準備します：

1. 撮影した麻雀牌の画像を `raw_images/` などのフォルダに保存

2. 画像整理ツールを使用して牌タイプごとに分類
   ```bash
   python tools/organize_tile_images.py --input_dir=./raw_images --output_dir=./dataset/tiles --interactive
   ```

3. 整理されたデータセットをトレーニングに使用
   ```bash
   python tools/train_tile_recognition.py --data_dir=./dataset/tiles --epochs=50
   ```

## 推奨事項

- 各牌タイプごとに50枚以上の画像を用意することを推奨
- 様々な角度・照明条件で撮影すると精度が向上
- 雀魂（じゃんたま/Mahjong Soul）の見た目に近い画像を使用する
