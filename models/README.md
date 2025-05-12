# 学習済みモデルディレクトリ

このディレクトリには、麻雀アシスタントで使用する学習済みの機械学習モデルを格納します。

## モデル一覧

- **tile_recognition_model/** - 牌認識用のモデル
  - TensorFlow SavedModel形式のモデル
  - 入力：64x64ピクセルのRGB画像
  - 出力：34クラス（牌種）の確率分布

## モデルの準備方法

### 牌認識モデルのトレーニング

1. データセットの準備
   - 雀魂の画面からキャプチャした各種牌の画像を収集
   - 各牌タイプごとに100枚以上のサンプルを用意
   - 画像は64x64ピクセルにリサイズ

2. トレーニングスクリプトの実行
   ```
   python train_tile_recognition.py --data_dir=dataset/tiles --epochs=50 --batch_size=32
   ```

3. モデルのエクスポート
   ```
   python export_model.py --checkpoint=checkpoints/best --output_dir=models/tile_recognition_model
   ```

## 注意事項

- このディレクトリには大容量のモデルファイルが含まれるため、Git LFS（Large File Storage）の使用を推奨します
- モデルファイルは定期的に更新し、精度を向上させることが重要です
