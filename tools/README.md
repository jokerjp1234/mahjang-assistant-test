# 麻雀牌認識ツール

このディレクトリには、麻雀牌認識の機械学習モデルを作成・訓練するためのツールが含まれています。

## 主なツール

- `organize_tile_images.py` - 撮影した牌画像をタイプごとに整理するツール
- `train_tile_recognition.py` - 牌認識用の機械学習モデルをトレーニングするツール
- `export_model.py` - トレーニング済みモデルをエクスポートするツール

## 使用方法

### Step 1: 牌画像の整理

まず、撮影した麻雀牌の画像を整理します。画像は各牌タイプごとのフォルダに分類されます。

```bash
# 対話モードで画像を確認しながら整理
python tools/organize_tile_images.py --input_dir=./raw_images --output_dir=./dataset/tiles --interactive

# ファイル名から自動で整理（ファイル名の先頭に牌タイプのIDをつける必要があります）
python tools/organize_tile_images.py --input_dir=./raw_images --output_dir=./dataset/tiles
```

#### 牌タイプIDの命名規則

- 萬子（マンズ）： `m1`, `m2`, ..., `m9`
- 筒子（ピンズ）： `p1`, `p2`, ..., `p9`
- 索子（ソウズ）： `s1`, `s2`, ..., `s9`
- 字牌（ジハイ）：
  - 風牌： `zeast`（東）, `zsouth`（南）, `zwest`（西）, `znorth`（北）
  - 三元牌： `zwhite`（白）, `zgreen`（發）, `zred`（中）

### Step 2: モデルのトレーニング

整理した画像データセットを使用して牌認識モデルをトレーニングします。

```bash
python tools/train_tile_recognition.py --data_dir=./dataset/tiles --epochs=50 --batch_size=32 --image_size=64x64
```

#### 主なオプション

- `--data_dir` - 整理された牌画像データセットのディレクトリ
- `--output_dir` - トレーニング済みモデルの出力先ディレクトリ
- `--epochs` - トレーニングのエポック数
- `--batch_size` - バッチサイズ
- `--validation_split` - 検証データの割合
- `--learning_rate` - 学習率
- `--image_size` - 画像サイズ（例: 64x64）

### Step 3: モデルのエクスポート

トレーニング済みモデルをアプリケーションで使用できる形式にエクスポートします。

```bash
python tools/export_model.py --model_path=models/tile_recognition_model/best_model.h5 --output_dir=models/exported_model
```

#### 主なオプション

- `--model_path` - トレーニング済みモデルのパス
- `--output_dir` - エクスポートしたモデルの出力先ディレクトリ
- `--image_size` - 画像サイズ（例: 64x64）

## データセットの推奨事項

- 各牌タイプごとに少なくとも50枚以上の画像サンプルを用意することを推奨します
- 様々な角度、照明条件で撮影すると、モデルの汎化性能が向上します
- 実際のアプリケーション環境に近い条件で撮影するのが望ましいです

## 注意事項

- このツールは学習・研究目的で作成されています
- 認識精度はデータセットの品質と量に大きく依存します
