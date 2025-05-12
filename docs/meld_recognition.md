# 副露（鳴き）認識機能

このドキュメントでは、麻雀アシスタントの副露（鳴き）認識機能について説明します。

## 副露認識の概要

副露（鳴き）とは、他のプレイヤーが捨てた牌を使って手牌から牌を公開することです。主な種類は以下の通りです：

- **チー（順子）**: 他家が捨てた牌と自分の手牌の連続する2枚を組み合わせて作る3枚の順子
- **ポン（刻子）**: 他家が捨てた牌と自分の手牌の同じ牌2枚を組み合わせて作る3枚の刻子
- **明カン（大明槓）**: 他家が捨てた牌と自分の手牌の同じ牌3枚を組み合わせて作る4枚の槓子
- **加槓（小明槓）**: 既に副露しているポンに同じ牌を追加して4枚にする
- **暗槓（暗カン）**: 自分の手牌だけで作る4枚の槓子

## 副露対応の新機能

新しい麻雀牌認識システムでは、以下の機能が追加されました：

1. **副露の自動検出**: 画面から各プレイヤーの副露状態を検出し、種類（チー、ポン、カン）を判別します
2. **手牌エリアの自動調整**: 副露数に応じて手牌の表示位置が変わるため、自動的に認識エリアを調整します
3. **ツモ牌位置の自動調整**: 副露数に応じてツモ牌の位置も変わるため、自動的に位置を調整します
4. **副露牌の認識**: 副露された牌も認識し、戦略提案に利用します

## 実装クラス

### MeldRecognizer クラス

`recognizer/meld_recognizer.py` に実装された副露認識専用のクラスです。

主な機能：
- 画面から副露エリアを検出
- 副露タイプの判別（チー、ポン、カン）
- 副露数に応じた手牌エリアとツモ牌位置の調整

### EnhancedMahjongRecognizer クラス

`recognizer/enhanced_recognizer.py` に実装された副露対応の拡張牌認識クラスです。

MahjongSoulRecognizer クラスの機能を拡張し、以下の機能を追加しています：
- 副露認識機能の統合
- 副露に応じた手牌枚数の調整
- 全プレイヤーの副露状態の追跡
- 副露牌も含めた可視牌の集計

## 使用方法

### 基本的な使い方

```python
from recognizer.enhanced_recognizer import EnhancedMahjongRecognizer

# 拡張牌認識クラスを初期化
recognizer = EnhancedMahjongRecognizer()

# ゲーム状態の検出（副露情報も含む）
game_state = recognizer.detect_game_state()

# 手牌の認識
hand_tiles = recognizer.recognize_hand_tiles(game_state['hand_img'])

# ツモ牌の認識
draw_tile = recognizer.recognize_draw_tile()

# 自分の副露牌の認識
my_meld_tiles = recognizer.recognize_meld_tiles(0)  # 0=自家

# 相手の副露牌の認識
opponent_meld_tiles = recognizer.recognize_meld_tiles(2)  # 2=対面
```

### 副露数の取得

```python
# 自分の副露数を取得
own_meld_count = len(game_state['player_melds'][0])

# 対面の副露数を取得
opponent_meld_count = len(game_state['player_melds'][2])
```

### 全ての可視牌の取得

副露牌も含めて、現在ゲーム内で見えている全ての牌を取得できます。

```python
# 全ての可視牌を取得（牌種別ごとの枚数）
visible_tiles = recognizer.get_all_visible_tiles()

# 例: 1萬が何枚見えているか
man1_count = visible_tiles.get(0, 0)  # 0=1萬の牌種ID
```

## 注意事項

1. 副露検出の精度はゲーム画面の解像度や表示設定に依存します。最適な結果を得るためには、設定の調整が必要な場合があります。

2. 雀魂（じゃんたま/Mahjong Soul）の画面レイアウトに最適化されています。他の麻雀ゲームでは位置調整が必要です。

3. デモモードでは実際の画像認識を行わず、副露の振る舞いをシミュレートします。

## 今後の改善予定

- 副露の種類（チー、ポン、カン）の精度向上
- 副露牌自体の認識精度の向上
- より多様な画面レイアウトへの対応
- 鳴き判断支援機能の追加（鳴くべきかどうかの提案）
