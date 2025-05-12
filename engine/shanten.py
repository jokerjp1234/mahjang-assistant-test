#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シャンテン数計算モジュール
"""

import logging
from collections import defaultdict

logger = logging.getLogger("MahjongAssistant.Engine.Shanten")


class ShantenCalculator:
    """シャンテン数計算クラス"""
    
    def __init__(self):
        """初期化"""
        # 牌の種類数
        self.num_tiles = 34
        
        logger.info("ShantenCalculator初期化完了")
    
    def calculate_shanten(self, hand, melds=None):
        """
        シャンテン数を計算
        
        Parameters
        ----------
        hand : list
            手牌の配列（34形式）
        melds : list, optional
            副露のリスト
            
        Returns
        -------
        int
            シャンテン数
        """
        if melds is None:
            melds = []
        
        # 牌の枚数チェック
        if sum(hand) + len(melds) * 3 > 14:
            logger.warning(f"手牌の枚数が不正: {sum(hand)} + {len(melds) * 3}")
            return 8  # 不正な手牌
        
        # 通常手（4面子1雀頭）のシャンテン数を計算
        normal_shanten = self._calculate_normal_shanten(hand, melds)
        
        # 七対子のシャンテン数を計算
        chitoitsu_shanten = self._calculate_chitoitsu_shanten(hand)
        
        # 国士無双のシャンテン数を計算
        kokushi_shanten = self._calculate_kokushi_shanten(hand)
        
        # 最小値を返す
        return min(normal_shanten, chitoitsu_shanten, kokushi_shanten)
    
    def _calculate_normal_shanten(self, hand, melds):
        """
        通常手（4面子1雀頭）のシャンテン数を計算
        
        Parameters
        ----------
        hand : list
            手牌の配列（34形式）
        melds : list
            副露のリスト
            
        Returns
        -------
        int
            シャンテン数
        """
        # 面子の数
        mentsu_count = len(melds)
        
        # 雀頭候補の数
        pair_count = 0
        
        # 塔子（ターツ：順子の2枚）の数
        taatsu_count = 0
        
        # 孤立牌（単騎待ちの牌）の数
        isolated_count = 0
        
        # 各種族ごとに計算
        for suit in range(3):  # 萬子、筒子、索子
            # 刻子（コーツ：同じ牌3枚）を優先的に抽出
            for i in range(9):
                idx = suit * 9 + i
                if hand[idx] >= 3:
                    mentsu_count += 1
                    hand[idx] -= 3
            
            # 順子（シュンツ：連続する3枚）を抽出
            for i in range(7):
                idx = suit * 9 + i
                while hand[idx] > 0 and hand[idx + 1] > 0 and hand[idx + 2] > 0:
                    mentsu_count += 1
                    hand[idx] -= 1
                    hand[idx + 1] -= 1
                    hand[idx + 2] -= 1
            
            # 雀頭候補を抽出
            for i in range(9):
                idx = suit * 9 + i
                if hand[idx] >= 2:
                    pair_count += 1
                    hand[idx] -= 2
            
            # 塔子（ターツ）を抽出
            for i in range(8):
                idx = suit * 9 + i
                if hand[idx] > 0 and hand[idx + 1] > 0:
                    taatsu_count += 1
                    hand[idx] -= 1
                    hand[idx + 1] -= 1
            
            # 孤立牌をカウント
            for i in range(9):
                idx = suit * 9 + i
                isolated_count += hand[idx]
        
        # 字牌（風牌、三元牌）の処理
        for i in range(27, 34):
            if hand[i] >= 3:
                mentsu_count += 1
                hand[i] -= 3
            if hand[i] >= 2:
                pair_count += 1
                hand[i] -= 2
            isolated_count += hand[i]
        
        # シャンテン数の計算
        # 4面子1雀頭の形にするためには、
        # 面子が4つと雀頭が1つ必要
        # 面子不足数 = 4 - 面子数
        # 雀頭不足数 = 1 - min(1, 雀頭候補数)
        # シャンテン数 = 面子不足数 + 雀頭不足数 - 待ち牌の数
        # ただし、面子不足を埋めるのに塔子は2枚で1面子になるので、
        # 待ち牌の数は min(面子不足数, 塔子の数) + 孤立牌が雀頭になる場合
        
        mentsu_needed = 4 - mentsu_count
        pair_needed = 1 if pair_count == 0 else 0
        
        # 面子不足を埋められる数
        fillable = min(mentsu_needed, taatsu_count)
        
        # シャンテン数の計算
        shanten = mentsu_needed + pair_needed - fillable
        
        return shanten
    
    def _calculate_chitoitsu_shanten(self, hand):
        """
        七対子のシャンテン数を計算
        
        Parameters
        ----------
        hand : list
            手牌の配列（34形式）
            
        Returns
        -------
        int
            シャンテン数
        """
        # 対子の数
        pair_count = sum(1 for x in hand if x >= 2)
        
        # 七対子は7つの対子が必要
        # シャンテン数 = 6 - 対子の数
        return 6 - pair_count
    
    def _calculate_kokushi_shanten(self, hand):
        """
        国士無双のシャンテン数を計算
        
        Parameters
        ----------
        hand : list
            手牌の配列（34形式）
            
        Returns
        -------
        int
            シャンテン数
        """
        # 国士無双の牌
        kokushi_tiles = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
        
        # 国士無双の牌の種類数
        unique_count = sum(1 for tile_id in kokushi_tiles if hand[tile_id] > 0)
        
        # 国士無双の雀頭候補
        has_pair = any(hand[tile_id] >= 2 for tile_id in kokushi_tiles)
        
        # 国士無双は13種類の幺九牌が必要
        # シャンテン数 = 13 - 幺九牌の種類数 - (雀頭があれば1、なければ0)
        return 13 - unique_count - (1 if has_pair else 0)
    
    def calculate_effective_tiles(self, hand, melds=None):
        """
        有効牌を計算
        
        Parameters
        ----------
        hand : list
            手牌の配列（34形式）
        melds : list, optional
            副露のリスト
            
        Returns
        -------
        list
            有効牌のリスト（34形式）
        """
        if melds is None:
            melds = []
        
        # 現在のシャンテン数を計算
        current_shanten = self.calculate_shanten(hand.copy(), melds)
        
        # 有効牌を探索
        effective_tiles = []
        for tile_id in range(self.num_tiles):
            # この牌がすでに4枚使われていたらスキップ
            if hand[tile_id] >= 4:
                continue
            
            # この牌を追加した場合の手牌
            new_hand = hand.copy()
            new_hand[tile_id] += 1
            
            # 1枚追加するのでどこかの牌を減らす必要がある
            for i in range(self.num_tiles):
                if new_hand[i] > 0:
                    new_hand[i] -= 1
                    
                    # 追加後のシャンテン数を計算
                    new_shanten = self.calculate_shanten(new_hand.copy(), melds)
                    
                    # シャンテン数が下がる牌を有効牌とする
                    if new_shanten < current_shanten and tile_id not in effective_tiles:
                        effective_tiles.append(tile_id)
                    
                    # 元に戻す
                    new_hand[i] += 1
        
        return effective_tiles
