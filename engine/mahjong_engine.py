#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀戦略エンジン

このモジュールは、牌認識結果から最適な打牌戦略を決定するロジックを提供します。
シャンテン数の計算、有効牌の判定、危険牌の判定などの機能を実装しています。
"""

import os
import sys
import numpy as np
from collections import Counter


class MahjongEngine:
    """麻雀戦略エンジンクラス"""
    
    # 牌の種類
    TYPES = {
        # 萬子 (manzu)
        'm1': 0, 'm2': 1, 'm3': 2, 'm4': 3, 'm5': 4, 'm6': 5, 'm7': 6, 'm8': 7, 'm9': 8,
        # 筒子 (pinzu)
        'p1': 9, 'p2': 10, 'p3': 11, 'p4': 12, 'p5': 13, 'p6': 14, 'p7': 15, 'p8': 16, 'p9': 17,
        # 索子 (souzu)
        's1': 18, 's2': 19, 's3': 20, 's4': 21, 's5': 22, 's6': 23, 's7': 24, 's8': 25, 's9': 26,
        # 字牌 (jihai)
        'zeast': 27, 'zsouth': 28, 'zwest': 29, 'znorth': 30, 'zwhite': 31, 'zgreen': 32, 'zred': 33
    }
    
    # 牌IDから表示名へのマッピング
    TILE_NAMES = {
        # 萬子 (manzu)
        'm1': '一萬', 'm2': '二萬', 'm3': '三萬', 'm4': '四萬', 'm5': '五萬',
        'm6': '六萬', 'm7': '七萬', 'm8': '八萬', 'm9': '九萬',
        # 筒子 (pinzu)
        'p1': '一筒', 'p2': '二筒', 'p3': '三筒', 'p4': '四筒', 'p5': '五筒',
        'p6': '六筒', 'p7': '七筒', 'p8': '八筒', 'p9': '九筒',
        # 索子 (souzu)
        's1': '一索', 's2': '二索', 's3': '三索', 's4': '四索', 's5': '五索',
        's6': '六索', 's7': '七索', 's8': '八索', 's9': '九索',
        # 字牌 (jihai)
        'zeast': '東', 'zsouth': '南', 'zwest': '西', 'znorth': '北',
        'zwhite': '白', 'zgreen': '發', 'zred': '中'
    }
    
    def __init__(self):
        """初期化"""
        # ゲーム状態
        self.hand = []          # 手牌
        self.visible_tiles = {} # 見えている牌（河や副露）
        self.dora = []          # ドラ表示牌
        self.discards = []      # 自分の捨て牌
        self.melds = []         # 自分の副露
        
        # 牌の残り枚数（理論値）
        self.remaining_tiles = {tile_id: 4 for tile_id in self.TYPES.keys()}
    
    def set_hand(self, hand_tiles):
        """
        手牌を設定する
        
        Parameters
        ----------
        hand_tiles : list
            手牌のリスト（牌ID）
        """
        self.hand = list(hand_tiles)
    
    def set_melds(self, meld_tiles):
        """
        副露を設定する
        
        Parameters
        ----------
        meld_tiles : list
            副露牌のリスト（牌ID）
        """
        self.melds = list(meld_tiles)
    
    def add_visible_tiles(self, tiles):
        """
        見えている牌を追加する
        
        Parameters
        ----------
        tiles : list or dict
            見えている牌のリストまたは辞書（牌ID: 枚数）
        """
        if isinstance(tiles, list):
            # リストの場合はカウント
            for tile in tiles:
                if tile in self.visible_tiles:
                    self.visible_tiles[tile] += 1
                else:
                    self.visible_tiles[tile] = 1
        elif isinstance(tiles, dict):
            # 辞書の場合はマージ
            for tile, count in tiles.items():
                if tile in self.visible_tiles:
                    self.visible_tiles[tile] += count
                else:
                    self.visible_tiles[tile] = count
    
    def set_dora(self, dora_tiles):
        """
        ドラ表示牌を設定する
        
        Parameters
        ----------
        dora_tiles : list
            ドラ表示牌のリスト（牌ID）
        """
        self.dora = list(dora_tiles)
    
    def add_discard(self, tile):
        """
        捨て牌を追加する
        
        Parameters
        ----------
        tile : str
            捨てた牌のID
        """
        self.discards.append(tile)
        
        # 見えている牌に追加
        if tile in self.visible_tiles:
            self.visible_tiles[tile] += 1
        else:
            self.visible_tiles[tile] = 1
    
    def update_remaining_tiles(self):
        """残り牌数を更新する"""
        # 初期化
        self.remaining_tiles = {tile_id: 4 for tile_id in self.TYPES.keys()}
        
        # 手牌を減算
        for tile in self.hand:
            if tile in self.remaining_tiles:
                self.remaining_tiles[tile] -= 1
        
        # 副露を減算
        for tile in self.melds:
            if tile in self.remaining_tiles:
                self.remaining_tiles[tile] -= 1
        
        # 見えている牌を減算
        for tile, count in self.visible_tiles.items():
            if tile in self.remaining_tiles:
                self.remaining_tiles[tile] -= min(count, self.remaining_tiles[tile])
    
    def calculate_shanten(self, tiles=None):
        """
        シャンテン数を計算する
        
        Parameters
        ----------
        tiles : list, optional
            計算対象の牌リスト。Noneの場合は現在の手牌を使用
            
        Returns
        -------
        int
            シャンテン数（0: テンパイ、-1: 和了、n: n向聴）
        """
        if tiles is None:
            tiles = self.hand
        
        # 簡易的なシャンテン計算（実際の麻雀では複雑なアルゴリズムが必要）
        # この実装は簡略化されており、正確なシャンテン数を計算するものではありません
        
        # 牌の集計
        tile_counts = Counter(tiles)
        
        # 対子の数
        pairs = sum(1 for count in tile_counts.values() if count >= 2)
        
        # 順子の可能性（萬子、筒子、索子のみ）
        sequences = 0
        for suit in ['m', 'p', 's']:
            for i in range(1, 8):  # 1-7（9まで）
                if (f'{suit}{i}' in tile_counts and 
                    f'{suit}{i+1}' in tile_counts and 
                    f'{suit}{i+2}' in tile_counts):
                    sequences += 1
        
        # 暗刻の数
        triplets = sum(1 for count in tile_counts.values() if count >= 3)
        
        # セットの数（順子または暗刻）
        sets = sequences + triplets
        
        # 必要なセットと雀頭
        # 通常の和了形は4セット+1雀頭
        needed_sets = 4
        needed_pairs = 1
        
        # シャンテン数の計算
        # 必要なセット数 + 必要な雀頭数 - 現在のセット数 - min(現在の対子数, 必要な雀頭数)
        shanten = needed_sets + needed_pairs - sets - min(pairs, needed_pairs)
        
        return shanten
    
    def get_effective_tiles(self):
        """
        有効牌（シャンテン数を減らす牌）を取得する
        
        Returns
        -------
        dict
            牌ID: 改善度のマッピング
        """
        # 現在のシャンテン数
        current_shanten = self.calculate_shanten()
        
        effective_tiles = {}
        
        # すべての牌タイプについて試す
        for tile_id in self.TYPES.keys():
            # この牌がまだ残っているか確認
            if self.remaining_tiles.get(tile_id, 0) <= 0:
                continue
            
            # この牌を加えた場合のシャンテン数
            test_hand = self.hand + [tile_id]
            
            # 手牌が14枚になるので、各牌を捨てる場合を試す
            for i, discard in enumerate(test_hand):
                test_tiles = test_hand.copy()
                test_tiles.pop(i)  # 捨てる牌を除外
                
                # 新しいシャンテン数
                new_shanten = self.calculate_shanten(test_tiles)
                
                # シャンテン数が減る場合
                if new_shanten < current_shanten:
                    improvement = current_shanten - new_shanten
                    
                    # 有効牌として登録
                    if tile_id in effective_tiles:
                        effective_tiles[tile_id] = max(effective_tiles[tile_id], improvement)
                    else:
                        effective_tiles[tile_id] = improvement
        
        return effective_tiles
    
    def suggest_discard(self):
        """
        最適な捨て牌を提案する
        
        Returns
        -------
        dict
            提案結果を含む辞書
            - 'discard': 推奨する捨て牌
            - 'reason': 理由
            - 'shanten': 捨てた後のシャンテン数
            - 'effective_tiles': 有効牌のリスト
        """
        # 手牌が空の場合
        if not self.hand:
            return {
                'discard': None,
                'reason': '手牌がありません',
                'shanten': -1,
                'effective_tiles': {}
            }
        
        # 残り牌数の更新
        self.update_remaining_tiles()
        
        # 各牌を捨てた場合のシャンテン数とその後の有効牌を計算
        discard_options = {}
        
        for i, tile in enumerate(self.hand):
            # この牌を捨てた場合の手牌
            test_hand = self.hand.copy()
            test_hand.pop(i)
            
            # シャンテン数の計算
            shanten = self.calculate_shanten(test_hand)
            
            # 一時的に手牌を変更してシミュレーション
            original_hand = self.hand
            self.hand = test_hand
            
            # 有効牌の計算
            effective_tiles = self.get_effective_tiles()
            
            # 有効牌の合計枚数
            total_effective = sum(
                min(count, self.remaining_tiles.get(tile_id, 0))
                for tile_id, count in effective_tiles.items()
            )
            
            # 手牌を元に戻す
            self.hand = original_hand
            
            # オプションとして記録
            discard_options[tile] = {
                'shanten': shanten,
                'effective_tiles': effective_tiles,
                'total_effective': total_effective
            }
        
        # 最もシャンテン数が低く、有効牌が多い選択肢を選ぶ
        best_discard = None
        best_shanten = float('inf')
        best_effective = -1
        
        for tile, option in discard_options.items():
            # シャンテン数が低い方を優先
            if option['shanten'] < best_shanten:
                best_discard = tile
                best_shanten = option['shanten']
                best_effective = option['total_effective']
            # シャンテン数が同じなら有効牌が多い方を優先
            elif option['shanten'] == best_shanten and option['total_effective'] > best_effective:
                best_discard = tile
                best_effective = option['total_effective']
        
        # 結果の作成
        if best_discard is not None:
            option = discard_options[best_discard]
            
            # 理由の作成
            if option['shanten'] == 0:
                reason = "テンパイに必要"
            else:
                reason = f"{option['shanten']}向聴、有効牌{option['total_effective']}枚"
            
            return {
                'discard': best_discard,
                'reason': reason,
                'shanten': option['shanten'],
                'effective_tiles': option['effective_tiles']
            }
        else:
            return {
                'discard': self.hand[0] if self.hand else None,
                'reason': '最適な捨て牌が見つかりません',
                'shanten': -1,
                'effective_tiles': {}
            }
    
    def get_dangerous_tiles(self, opponent_discards=None):
        """
        危険牌（他家の待ちの可能性が高い牌）を判定する
        
        Parameters
        ----------
        opponent_discards : list, optional
            相手の捨て牌リスト
            
        Returns
        -------
        dict
            牌ID: 危険度のマッピング（0-100）
        """
        # 相手の捨て牌から推測
        danger_tiles = {}
        
        # 相手の捨て牌情報がある場合
        if opponent_discards:
            # 数牌（萬子、筒子、索子）の分析
            for suit in ['m', 'p', 's']:
                # 各数字の捨牌枚数
                discarded = {i: 0 for i in range(1, 10)}
                
                # 捨て牌を集計
                for tile in opponent_discards:
                    if tile.startswith(suit) and len(tile) == 2:
                        num = int(tile[1])
                        if 1 <= num <= 9:
                            discarded[num] += 1
                
                # 未登場の数字は危険の可能性
                for i in range(1, 10):
                    if discarded[i] == 0:
                        # 特に両面待ちになりやすい牌は危険
                        if 2 <= i <= 8:
                            # 周囲の牌も捨てられていない場合、さらに危険
                            if i > 2 and discarded[i-2] == 0:
                                danger_tiles[f'{suit}{i}'] = 80
                            elif i < 8 and discarded[i+2] == 0:
                                danger_tiles[f'{suit}{i}'] = 80
                            else:
                                danger_tiles[f'{suit}{i}'] = 60
                        else:
                            danger_tiles[f'{suit}{i}'] = 40
            
            # 字牌の分析
            for tile_id in ['zeast', 'zsouth', 'zwest', 'znorth', 'zwhite', 'zgreen', 'zred']:
                if tile_id not in opponent_discards:
                    danger_tiles[tile_id] = 50
        
        # リーチがかかっている場合、全ての残り牌を危険とする
        # （この実装は簡略化のため、実際にはもっと複雑な判定が必要）
        
        # 危険度の調整（手牌に含まれる牌は安全）
        for tile in self.hand:
            if tile in danger_tiles:
                danger_tiles[tile] = 0
        
        return danger_tiles
    
    def should_call_mahjong(self, winning_tile):
        """
        和了するべきかを判定する（役判定）
        
        Parameters
        ----------
        winning_tile : str
            和了牌のID
            
        Returns
        -------
        dict
            和了判定の結果
            - 'should_call': 和了するべきか（True/False）
            - 'yaku': 成立している役のリスト
            - 'score': 点数
        """
        # 簡易的な役判定（実際の麻雀では複雑な判定が必要）
        yaku = []
        score = 0
        
        # 手牌＋和了牌
        complete_hand = self.hand + [winning_tile]
        
        # 七対子の判定
        if len(complete_hand) == 14:
            tile_counts = Counter(complete_hand)
            if all(count == 2 for count in tile_counts.values()):
                yaku.append('七対子')
                score = 25
        
        # 他の役判定（簡略化）
        # 通常は役満、三色同順、一気通貫など様々な役を判定する
        
        # 結果の判定
        should_call = len(yaku) > 0
        
        return {
            'should_call': should_call,
            'yaku': yaku,
            'score': score
        }
    
    def should_call_riichi(self):
        """
        リーチするべきかを判定する
        
        Returns
        -------
        dict
            リーチ判定の結果
            - 'should_call': リーチするべきか（True/False）
            - 'discard': リーチ宣言牌
            - 'reason': 理由
        """
        # 手牌のシャンテン数を確認
        shanten = self.calculate_shanten()
        
        # テンパイしていない場合はリーチできない
        if shanten > 0:
            return {
                'should_call': False,
                'discard': None,
                'reason': f'テンパイしていません（{shanten}向聴）'
            }
        
        # テンパイしている場合、最適な捨て牌を選ぶ
        suggestion = self.suggest_discard()
        
        # ベンチマーク: 有効牌の残り枚数
        effective_count = sum(
            min(count, self.remaining_tiles.get(tile_id, 0))
            for tile_id, count in suggestion['effective_tiles'].items()
        )
        
        # 有効牌が少なすぎる場合はリーチしない
        if effective_count < 4:
            return {
                'should_call': False,
                'discard': suggestion['discard'],
                'reason': f'有効牌が少なすぎます（{effective_count}枚）'
            }
        
        # 残り牌数が少ない場合はリーチしない（ここでは簡易的な判定）
        remaining_total = sum(self.remaining_tiles.values())
        if remaining_total < 20:
            return {
                'should_call': False,
                'discard': suggestion['discard'],
                'reason': f'終盤なのでリーチは控えめに（残り{remaining_total}枚）'
            }
        
        # その他の判定（点数状況や局面など）
        
        # リーチを推奨
        return {
            'should_call': True,
            'discard': suggestion['discard'],
            'reason': f'有効牌{effective_count}枚、リーチ推奨'
        }
    
    def should_call_chi_pon_kan(self, tile, call_type):
        """
        チー/ポン/カンするべきかを判定する
        
        Parameters
        ----------
        tile : str
            鳴こうとしている牌のID
        call_type : str
            鳴きの種類（'chi', 'pon', 'kan'）
            
        Returns
        -------
        dict
            鳴き判定の結果
            - 'should_call': 鳴くべきか（True/False）
            - 'reason': 理由
        """
        # チーの判定
        if call_type == 'chi':
            # 手牌からチーできるか確認
            can_chi = False
            chi_sets = []
            
            # 数牌の場合のみチー可能
            if tile[0] in ['m', 'p', 's'] and len(tile) == 2:
                tile_num = int(tile[1])
                suit = tile[0]
                
                # 左チー（例: 3,4 + 5）
                if tile_num >= 3:
                    left_tiles = [f'{suit}{tile_num-2}', f'{suit}{tile_num-1}']
                    if all(t in self.hand for t in left_tiles):
                        can_chi = True
                        chi_sets.append(left_tiles + [tile])
                
                # 中チー（例: 4 + 5 + 6）
                if 2 <= tile_num <= 8:
                    middle_tiles = [f'{suit}{tile_num-1}', f'{suit}{tile_num+1}']
                    if all(t in self.hand for t in middle_tiles):
                        can_chi = True
                        chi_sets.append([middle_tiles[0], tile, middle_tiles[1]])
                
                # 右チー（例: 5 + 6,7）
                if tile_num <= 7:
                    right_tiles = [f'{suit}{tile_num+1}', f'{suit}{tile_num+2}']
                    if all(t in self.hand for t in right_tiles):
                        can_chi = True
                        chi_sets.append([tile] + right_tiles)
            
            if not can_chi:
                return {
                    'should_call': False,
                    'reason': 'チーできる牌がありません'
                }
            
            # チーした場合のシャンテン数変化を確認
            current_shanten = self.calculate_shanten()
            best_improvement = 0
            best_set = None
            
            for chi_set in chi_sets:
                # チー後の手牌
                new_hand = self.hand.copy()
                for t in chi_set:
                    if t != tile and t in new_hand:
                        new_hand.remove(t)
                
                # シャンテン数の変化
                new_shanten = self.calculate_shanten(new_hand)
                improvement = current_shanten - new_shanten
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_set = chi_set
            
            # シャンテン数が改善する場合はチーを推奨
            if best_improvement > 0:
                return {
                    'should_call': True,
                    'reason': f'シャンテン数が{best_improvement}減少します'
                }
            
            # その他の判定（手牌の形や局面など）
            
            # 基本的にはチーを控える
            return {
                'should_call': False,
                'reason': 'シャンテン数の改善がないため、チーは控えめに'
            }
        
        # ポンの判定
        elif call_type == 'pon':
            # 手牌からポンできるか確認
            tile_count = self.hand.count(tile)
            
            if tile_count < 2:
                return {
                    'should_call': False,
                    'reason': 'ポンできる牌がありません'
                }
            
            # ポン後の手牌
            new_hand = self.hand.copy()
            for _ in range(2):  # 手牌から2枚除去
                new_hand.remove(tile)
            
            # シャンテン数の変化
            current_shanten = self.calculate_shanten()
            new_shanten = self.calculate_shanten(new_hand)
            improvement = current_shanten - new_shanten
            
            # シャンテン数が改善する場合はポンを推奨
            if improvement > 0:
                return {
                    'should_call': True,
                    'reason': f'シャンテン数が{improvement}減少します'
                }
            
            # 三元牌や場風はポンするメリットが高い
            if tile in ['zwhite', 'zgreen', 'zred', 'zeast']:
                return {
                    'should_call': True,
                    'reason': '役牌のポンは有利です'
                }
            
            # 基本的にはポンを控える
            return {
                'should_call': False,
                'reason': 'シャンテン数の改善がないため、ポンは控えめに'
            }
        
        # カンの判定
        elif call_type == 'kan':
            # 手牌からカンできるか確認
            tile_count = self.hand.count(tile)
            
            if tile_count < 3:
                return {
                    'should_call': False,
                    'reason': 'カンできる牌がありません'
                }
            
            # カン後の手牌（抜きカン）
            new_hand = self.hand.copy()
            for _ in range(3):  # 手牌から3枚除去
                new_hand.remove(tile)
            
            # シャンテン数の変化
            current_shanten = self.calculate_shanten()
            new_shanten = self.calculate_shanten(new_hand)
            improvement = current_shanten - new_shanten
            
            # シャンテン数が改善する場合はカンを推奨
            if improvement > 0:
                return {
                    'should_call': True,
                    'reason': f'シャンテン数が{improvement}減少します'
                }
            
            # 基本的にはカンを控える（リンシャンツモやドラ増加というメリットもある）
            return {
                'should_call': True,
                'reason': 'リンシャンツモとドラ増加が期待できます'
            }
        
        else:
            return {
                'should_call': False,
                'reason': f'不明な鳴き種類: {call_type}'
            }
    
    def get_tile_name(self, tile_id):
        """
        牌IDから表示名を取得する
        
        Parameters
        ----------
        tile_id : str
            牌ID
            
        Returns
        -------
        str
            牌の表示名
        """
        return self.TILE_NAMES.get(tile_id, tile_id)


# 簡単なテスト
if __name__ == "__main__":
    engine = MahjongEngine()
    
    # テスト用の手牌
    test_hand = ['m1', 'm2', 'm3', 'p2', 'p3', 'p4', 's5', 's5', 's5', 'zeast', 'zeast', 'zwhite', 'zwhite']
    engine.set_hand(test_hand)
    
    # シャンテン数
    shanten = engine.calculate_shanten()
    print(f"シャンテン数: {shanten}")
    
    # 捨て牌提案
    suggestion = engine.suggest_discard()
    print(f"提案する捨て牌: {engine.get_tile_name(suggestion['discard'])}")
    print(f"理由: {suggestion['reason']}")
    
    # 有効牌
    effective_tiles = suggestion['effective_tiles']
    if effective_tiles:
        print("有効牌:")
        for tile, improvement in effective_tiles.items():
            print(f"  {engine.get_tile_name(tile)}: {improvement}シャンテン改善")
