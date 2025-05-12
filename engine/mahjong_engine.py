#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀ロジックエンジン - 雀魂(Mahjong Soul)向け
"""

import os
import logging
import numpy as np
from collections import defaultdict

# 自作モジュールのインポート
from engine.shanten import ShantenCalculator

logger = logging.getLogger("MahjongAssistant.Engine")


class MahjongSoulEngine:
    """雀魂向け麻雀ロジックエンジン"""
    
    def __init__(self):
        """初期化"""
        # シャンテン数計算機の初期化
        self.shanten_calculator = ShantenCalculator()
        
        # 雀魂特有のルール設定
        self.red_dora_enabled = True  # 赤ドラあり
        self.open_tanyao_enabled = True  # 喰いタンあり
        self.akadora_count = 3  # 赤ドラ3枚（萬子・筒子・索子に各1枚）
        
        # 牌の種類数
        self.num_tiles = 34
        
        # 牌の残り枚数（ゲーム開始時）
        self.remaining_tiles = [4] * self.num_tiles
        
        # ゲーム状態
        self.game_state = {}
        
        logger.info("MahjongSoulEngine初期化完了")
    
    def calculate_shanten(self, hand_tiles, melds=None):
        """
        シャンテン数を計算
        
        Parameters
        ----------
        hand_tiles : list
            手牌のリスト（136形式）
        melds : list, optional
            副露のリスト
        
        Returns
        -------
        int
            シャンテン数
        """
        # 136形式から34形式に変換
        hand34 = self._to_34_array(hand_tiles)
        
        # メルドがない場合は空リストを使用
        if melds is None:
            melds = []
        
        try:
            # シャンテン数を計算
            return self.shanten_calculator.calculate_shanten(hand34, melds)
        except Exception as e:
            logger.error(f"シャンテン数計算中にエラー: {e}")
            # エラー時は適当な値を返す
            return 4
    
    def calculate_effective_tiles(self, hand_tiles, melds=None):
        """
        有効牌を計算
        
        Parameters
        ----------
        hand_tiles : list
            手牌のリスト（136形式）
        melds : list, optional
            副露のリスト
            
        Returns
        -------
        list
            有効牌のリスト（34形式）
        """
        # 136形式から34形式に変換
        hand34 = self._to_34_array(hand_tiles)
        
        # メルドがない場合は空リストを使用
        if melds is None:
            melds = []
            
        try:
            # 現在のシャンテン数を計算
            current_shanten = self.shanten_calculator.calculate_shanten(hand34, melds)
            
            # 有効牌を探索
            effective_tiles = []
            for tile_id in range(self.num_tiles):
                # この牌がすでに4枚使われていたらスキップ
                if hand34[tile_id] >= 4:
                    continue
                
                # この牌を追加した場合の手牌
                new_hand = hand34.copy()
                new_hand[tile_id] += 1
                
                # 追加後のシャンテン数を計算
                new_shanten = self.shanten_calculator.calculate_shanten(new_hand, melds)
                
                # シャンテン数が下がる牌を有効牌とする
                if new_shanten < current_shanten:
                    effective_tiles.append(tile_id)
            
            logger.debug(f"有効牌: {effective_tiles}")
            return effective_tiles
        except Exception as e:
            logger.error(f"有効牌計算中にエラー: {e}")
            # エラー時は適当な値を返す
            return []
    
    def calculate_best_discard(self, hand_tiles, dora_tiles, all_discards, melds=None):
        """
        最適な捨て牌を計算
        
        Parameters
        ----------
        hand_tiles : list
            手牌のリスト（136形式）
        dora_tiles : list
            ドラ表示牌のリスト（136形式）
        all_discards : list
            全員の捨て牌リスト（136形式）
        melds : list, optional
            副露のリスト
            
        Returns
        -------
        tuple
            (最適な捨て牌, 評価値)
        """
        if not hand_tiles:
            logger.warning("手牌が空です")
            return None, 0
        
        # メルドがない場合は空リストを使用
        if melds is None:
            melds = []
            
        try:
            # 各牌について捨てた場合の評価値を計算
            evaluations = []
            
            for tile in hand_tiles:
                # この牌を捨てた場合の手牌
                new_hand = hand_tiles.copy()
                new_hand.remove(tile)
                
                # 136形式から34形式に変換
                hand34 = self._to_34_array(new_hand)
                
                # シャンテン数計算
                shanten = self.shanten_calculator.calculate_shanten(hand34, melds)
                
                # 有効牌の数
                effective_tiles = []
                for tile_id in range(self.num_tiles):
                    # この牌がすでに4枚使われていたらスキップ
                    if hand34[tile_id] >= 4:
                        continue
                    
                    # この牌を追加した場合の手牌
                    test_hand = hand34.copy()
                    test_hand[tile_id] += 1
                    
                    # 追加後のシャンテン数を計算
                    test_shanten = self.shanten_calculator.calculate_shanten(test_hand, melds)
                    
                    # シャンテン数が下がる牌を有効牌とする
                    if test_shanten < shanten:
                        effective_tiles.append(tile_id)
                
                # 有効牌の残り枚数を計算
                remaining_count = sum(self._estimate_remaining_tiles(all_discards)[tile_id] for tile_id in effective_tiles)
                
                # 危険度（他家の捨て牌から推測）
                danger_level = self.calculate_danger(tile, all_discards, [False, False, False, False])
                
                # 得点期待値
                score_exp = self._calculate_expected_score(hand34, dora_tiles)
                
                # 総合評価（要調整）
                value = self._evaluate_discard(shanten, len(effective_tiles), remaining_count, danger_level, score_exp)
                
                # 結果を保存
                evaluations.append((tile, value))
            
            # 最も評価値の高い牌を選択
            best_tile, best_value = max(evaluations, key=lambda x: x[1])
            
            logger.debug(f"最適な捨て牌: {best_tile//4}{['萬', '筒', '索', '字'][best_tile//36]}, 評価値: {best_value:.2f}")
            return best_tile, best_value
        
        except Exception as e:
            logger.error(f"最適捨て牌計算中にエラー: {e}")
            # エラー時は手牌の先頭の牌を返す
            if hand_tiles:
                return hand_tiles[0], 0
            return None, 0
    
    def calculate_danger(self, tile, all_discards, reach_status):
        """
        牌の危険度を計算
        
        Parameters
        ----------
        tile : int
            評価する牌（136形式）
        all_discards : list
            全員の捨て牌リスト（136形式）
        reach_status : list
            各プレイヤーのリーチ状態
            
        Returns
        -------
        float
            危険度 (0-1の範囲、1が最も危険)
        """
        # 136形式から34形式に変換
        tile34 = tile // 4
        
        # 基本危険度
        danger = 0.0
        
        # リーチがかかっている場合は危険度を上げる
        if any(reach_status):
            # リーチしているプレイヤーの数
            reach_count = sum(reach_status)
            
            # リーチ者の河から危険度を算出
            for i, is_reach in enumerate(reach_status):
                if is_reach:
                    # このプレイヤーの捨て牌を抽出
                    player_discards = [t // 4 for t in all_discards]
                    
                    # 同種の牌が捨てられていれば安全度が上がる
                    same_type_discarded = player_discards.count(tile34)
                    danger = max(danger, 1.0 - (same_type_discarded / 4.0))
                    
                    # 筋の牌も考慮
                    if tile34 < 27:  # 数牌の場合
                        suit = tile34 // 9  # 0:萬子, 1:筒子, 2:索子
                        number = tile34 % 9  # 0-8
                        
                        # 筋の牌の牌種を計算
                        suji_tiles = []
                        if number <= 5:  # 1-6
                            suji_tiles.append(suit * 9 + number + 3)  # 例: 1->4, 2->5, ...
                        if number >= 3:  # 4-9
                            suji_tiles.append(suit * 9 + number - 3)  # 例: 4->1, 5->2, ...
                        
                        # 筋の牌が捨てられていれば安全度が上がる
                        for suji in suji_tiles:
                            if suji in player_discards:
                                danger -= 0.1
            
            # 複数人がリーチしている場合、危険度は高くなる
            danger *= (1.0 + 0.2 * (reach_count - 1))
        
        # 全体的な枯れ具合も考慮
        discarded_count = all_discards.count(tile) // 4
        danger -= 0.2 * discarded_count
        
        # 数牌の場合、位置による危険度調整
        if tile34 < 27:
            number = tile34 % 9  # 0-8
            
            # 1,9は比較的安全、2,8は中程度、3-7は危険
            if number == 0 or number == 8:  # 1,9
                danger -= 0.2
            elif number == 1 or number == 7:  # 2,8
                danger -= 0.1
        
        # 字牌は比較的安全
        else:
            danger -= 0.15
        
        # 0-1の範囲に正規化
        danger = max(0.0, min(1.0, danger))
        
        return danger
    
    def predict_opponent_waits(self, discards, melds, is_riichi):
        """
        相手の待ち牌を予測
        
        Parameters
        ----------
        discards : list
            対象プレイヤーの捨て牌リスト（136形式）
        melds : list
            対象プレイヤーの副露リスト
        is_riichi : bool
            対象プレイヤーがリーチしているかどうか
            
        Returns
        -------
        dict
            待ち牌とその確率の辞書 {牌ID: 確率}
        """
        if not is_riichi:
            # リーチしていない場合は予測精度が低いので空の辞書を返す
            return {}
        
        # ダミー実装: よくある待ち牌パターンを返す
        # 実際の実装では捨て牌履歴などから機械学習で推定
        waits = {
            8: 0.7,   # 3萬
            20: 0.2,  # 6筒
            64: 0.1   # 5索
        }
        
        return waits
    
    def _to_34_array(self, tiles):
        """
        136形式の牌リストを34形式の配列に変換
        
        Parameters
        ----------
        tiles : list
            変換する牌リスト（136形式）
            
        Returns
        -------
        list
            34形式の配列（インデックスが牌種、値が枚数）
        """
        result = [0] * 34
        for tile in tiles:
            result[tile // 4] += 1
        return result
    
    def _estimate_remaining_tiles(self, all_discards):
        """
        全ての捨て牌から残り牌を推定
        
        Parameters
        ----------
        all_discards : list
            全員の捨て牌リスト（136形式）
            
        Returns
        -------
        list
            各牌の残り枚数（34形式）
        """
        # 初期状態（各牌4枚ずつ）
        remaining = [4] * 34
        
        # 捨て牌を引く
        for tile in all_discards:
            tile34 = tile // 4
            remaining[tile34] = max(0, remaining[tile34] - 1)
        
        return remaining
    
    def _evaluate_discard(self, shanten, effective_tiles_count, remaining_count, danger, score_exp):
        """
        捨て牌の評価関数
        
        Parameters
        ----------
        shanten : int
            シャンテン数
        effective_tiles_count : int
            有効牌の種類数
        remaining_count : int
            有効牌の残り枚数
        danger : float
            危険度（0-1）
        score_exp : int
            期待得点
            
        Returns
        -------
        float
            評価値
        """
        # シャンテン数は低いほど良い、有効牌は多いほど良い、危険度は低いほど良い
        # 各項目に重みを付けて評価
        # 評価関数は調整が必要
        
        # シャンテン数の重み
        shanten_weight = -1.5
        
        # 有効牌の種類数の重み
        effective_tiles_weight = 0.3
        
        # 有効牌の残り枚数の重み
        remaining_weight = 0.2
        
        # 危険度の重み
        danger_weight = -0.7
        
        # 期待得点の重み（単位を合わせるため1/1000）
        score_weight = 0.1 / 1000
        
        # 総合評価
        value = (shanten_weight * shanten +
                 effective_tiles_weight * effective_tiles_count +
                 remaining_weight * remaining_count +
                 danger_weight * danger +
                 score_weight * score_exp)
        
        return value
    
    def _calculate_expected_score(self, hand34, dora_tiles):
        """
        期待得点を計算
        
        Parameters
        ----------
        hand34 : list
            手牌の配列（34形式）
        dora_tiles : list
            ドラ表示牌のリスト（136形式）
            
        Returns
        -------
        int
            期待得点
        """
        # ダミー実装: 役の有無をチェックして得点を推定
        # 実際の実装ではもっと精緻な計算が必要
        
        # 基本点
        expected_score = 1000
        
        # 対子の数をカウント
        pair_count = sum(1 for x in hand34 if x >= 2)
        
        # 刻子（暗刻）の数をカウント
        triplet_count = sum(1 for x in hand34 if x >= 3)
        
        # 順子の可能性（単純化）
        sequence_possibility = 0
        for suit in range(3):  # 萬子、筒子、索子
            for i in range(7):  # 1-7（これに続く8,9を考慮）
                idx = suit * 9 + i
                if hand34[idx] > 0 and hand34[idx + 1] > 0 and hand34[idx + 2] > 0:
                    sequence_possibility += 1
        
        # 役牌の価値
        yakuhai_value = 0
        for i in range(27, 34):  # 東、南、西、北、白、發、中
            if hand34[i] >= 3:
                yakuhai_value += 1000
        
        # ドラの数
        dora_count = 0
        for tile in dora_tiles:
            dora_id = (tile // 4 + 1) % 9 + (tile // 36) * 9  # 次の牌がドラ
            dora_count += hand34[dora_id]
        
        # 点数の調整
        expected_score += pair_count * 100
        expected_score += triplet_count * 400
        expected_score += sequence_possibility * 300
        expected_score += yakuhai_value
        expected_score += dora_count * 1000
        
        return expected_score
    
    def is_tenpai(self, hand_tiles, melds=None):
        """
        テンパイかどうかを判定
        
        Parameters
        ----------
        hand_tiles : list
            手牌のリスト（136形式）
        melds : list, optional
            副露のリスト
            
        Returns
        -------
        bool
            テンパイならTrue
        """
        # シャンテン数が0ならテンパイ
        return self.calculate_shanten(hand_tiles, melds) == 0
