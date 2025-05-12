#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀牌認識拡張モジュール - 副露（鳴き）対応版
"""

import os
import logging
import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
import json

logger = logging.getLogger("MahjongAssistant.Recognizer.Calls")


class MeldRecognizer:
    """
    副露（鳴き）検出・認識クラス
    
    このクラスは、雀魂の画面から副露（チー、ポン、カン）を検出し、
    副露に応じて手牌やツモ牌の位置を調整します。
    """
    
    def __init__(self, model_dir=None):
        """
        初期化
        
        Parameters
        ----------
        model_dir : str, optional
            モデルディレクトリ。Noneの場合は既定のパスが使用される。
        """
        # モデルディレクトリの設定
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "../models/tile_recognition_model")
        
        self.model_dir = Path(model_dir)
        
        # モデルのロード
        self.model = None
        if (self.model_dir / "saved_model").exists():
            try:
                self.model = tf.saved_model.load(str(self.model_dir / "saved_model"))
                logger.info("副露認識モデルを読み込みました")
            except Exception as e:
                logger.error(f"副露認識モデルのロードに失敗: {e}")
        
        # クラスマッピングの読み込み
        self.class_mapping = self._load_class_mapping()
        
        # 副露タイプの定義
        self.meld_types = {
            'chi': 0,    # チー
            'pon': 1,    # ポン
            'kan': 2,    # 明カン（大明槓）
            'ankan': 3,  # 暗カン
            'addon': 4   # 加槓
        }
        
        # 副露領域の設定
        self.meld_areas = [
            # 自分の副露エリア（最大4セット）
            [(1090, 650, 1140, 720),  # 1つ目の副露
             (1150, 650, 1200, 720),  # 2つ目の副露
             (1210, 650, 1260, 720),  # 3つ目の副露
             (1270, 650, 1320, 720)], # 4つ目の副露
            
            # 右家の副露エリア
            [(950, 540, 1020, 590),
             (950, 480, 1020, 530),
             (950, 420, 1020, 470),
             (950, 360, 1020, 410)],
            
            # 対面の副露エリア
            [(1090, 280, 1140, 350),
             (1150, 280, 1200, 350),
             (1210, 280, 1260, 350),
             (1270, 280, 1320, 350)],
            
            # 左家の副露エリア
            [(250, 360, 320, 410),
             (250, 420, 320, 470),
             (250, 480, 320, 530),
             (250, 540, 320, 590)]
        ]
        
        # 手牌とツモ牌の位置調整パラメータ
        self.hand_adjustment = {
            0: {"offset": 0, "width": 860},      # 副露なし: 標準位置
            1: {"offset": -80, "width": 780},    # 副露1セット: 位置調整
            2: {"offset": -160, "width": 700},   # 副露2セット: 位置調整
            3: {"offset": -240, "width": 620},   # 副露3セット: 位置調整
            4: {"offset": -320, "width": 540}    # 副露4セット: 位置調整
        }
        
        # ツモ牌位置の調整パラメータ
        self.draw_tile_adjustment = {
            0: {"x": 845, "y": 650, "width": 40, "height": 70},  # 副露なし
            1: {"x": 765, "y": 650, "width": 40, "height": 70},  # 副露1セット
            2: {"x": 685, "y": 650, "width": 40, "height": 70},  # 副露2セット
            3: {"x": 605, "y": 650, "width": 40, "height": 70},  # 副露3セット
            4: {"x": 525, "y": 650, "width": 40, "height": 70}   # 副露4セット
        }
    
    def _load_class_mapping(self):
        """
        クラスマッピングファイルを読み込む
        
        Returns
        -------
        dict
            クラスID -> 牌ID のマッピング辞書
        """
        mapping_file = self.model_dir / "class_mapping.txt"
        if not mapping_file.exists():
            logger.warning(f"クラスマッピングファイルが見つかりません: {mapping_file}")
            return self._default_class_mapping()
        
        try:
            mapping = {}
            with open(mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        idx = int(parts[0])
                        tile_id = parts[1]
                        mapping[idx] = tile_id
            return mapping
        except Exception as e:
            logger.error(f"クラスマッピングファイルの読み込みに失敗: {e}")
            return self._default_class_mapping()
    
    def _default_class_mapping(self):
        """
        デフォルトのクラスマッピングを返す
        
        Returns
        -------
        dict
            デフォルトのクラスID -> 牌ID マッピング
        """
        # 基本的な順序（萬子→筒子→索子→字牌）
        mapping = {}
        
        # 萬子
        for i in range(9):
            mapping[i] = f'm{i+1}'
        
        # 筒子
        for i in range(9):
            mapping[i+9] = f'p{i+1}'
        
        # 索子
        for i in range(9):
            mapping[i+18] = f's{i+1}'
        
        # 字牌
        mapping[27] = 'zeast'
        mapping[28] = 'zsouth'
        mapping[29] = 'zwest'
        mapping[30] = 'znorth'
        mapping[31] = 'zwhite'
        mapping[32] = 'zgreen'
        mapping[33] = 'zred'
        
        return mapping
    
    def detect_melds(self, screen):
        """
        画面から副露を検出する
        
        Parameters
        ----------
        screen : ndarray
            画面全体の画像
            
        Returns
        -------
        list
            各プレイヤーの副露情報のリスト
        """
        # 各プレイヤーの副露情報を格納するリスト
        player_melds = [[] for _ in range(4)]
        
        # 各プレイヤーの副露エリアを調べる
        for player_idx, player_meld_areas in enumerate(self.meld_areas):
            for meld_idx, meld_area in enumerate(player_meld_areas):
                x1, y1, x2, y2 = meld_area
                
                # 画像が範囲外にならないようにチェック
                if (x1 < 0 or y1 < 0 or 
                    x2 > screen.shape[1] or y2 > screen.shape[0]):
                    continue
                
                # 副露エリアの切り出し
                meld_img = screen[y1:y2, x1:x2]
                
                # 副露の検出
                meld_type, tiles = self._recognize_meld(meld_img)
                
                # 副露が検出されたら追加
                if meld_type is not None and tiles:
                    player_melds[player_idx].append({
                        'type': meld_type,
                        'tiles': tiles
                    })
        
        logger.debug(f"検出された副露: 自家={len(player_melds[0])}セット, "
                     f"右家={len(player_melds[1])}セット, "
                     f"対面={len(player_melds[2])}セット, "
                     f"左家={len(player_melds[3])}セット")
        
        return player_melds
    
    def _recognize_meld(self, meld_img):
        """
        副露画像から副露タイプと牌を認識する
        
        Parameters
        ----------
        meld_img : ndarray
            副露エリアの画像
            
        Returns
        -------
        tuple
            (副露タイプ, 牌リスト) のタプル。副露が検出されなければ (None, [])
        """
        # 副露の検出（画像の特徴から判断）
        # HSV色空間で牌の色の存在をチェック
        hsv = cv2.cvtColor(meld_img, cv2.COLOR_BGR2HSV)
        
        # 牌の色範囲（雀魂特有の色）
        tile_color_lower = np.array([20, 100, 100])  # 牌の色範囲（下限）HSV
        tile_color_upper = np.array([30, 255, 255])  # 牌の色範囲（上限）HSV
        
        # 色マスクを適用
        mask = cv2.inRange(hsv, tile_color_lower, tile_color_upper)
        
        # マスク内のピクセル数をカウント
        pixel_count = cv2.countNonZero(mask)
        
        # ピクセル数が少なすぎる場合は副露なしと判断
        if pixel_count < 100:
            return None, []
        
        # 副露タイプの判定
        # 実際の実装では、副露の見た目の特徴から判断する
        # ここではシンプルな判定ロジックを使用
        
        # 輪郭検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 輪郭の数と形状から副露タイプを判定
        if len(contours) == 0:
            return None, []
        
        # 大きな輪郭のみをフィルタリング
        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 200:  # 小さすぎる輪郭は無視
                valid_contours.append(cnt)
        
        # 有効な輪郭の数から副露タイプを推定
        if len(valid_contours) == 3:
            # 3つの輪郭ならチーまたはポン
            meld_type = 'chi'  # または 'pon'（正確な判別には形状分析が必要）
            tiles = ['m1', 'm2', 'm3']  # ダミーデータ（実際は認識結果）
        elif len(valid_contours) == 4:
            # 4つの輪郭なら明カン
            meld_type = 'kan'
            tiles = ['m1', 'm1', 'm1', 'm1']  # ダミーデータ
        else:
            # 判別できない場合
            return None, []
        
        # モデルがあれば牌の認識を行う
        if self.model is not None:
            # 牌の認識処理（実装が必要）
            pass
        
        return meld_type, tiles
    
    def adjust_hand_area(self, screen, meld_count):
        """
        副露数に応じて手牌エリアを調整する
        
        Parameters
        ----------
        screen : ndarray
            画面全体の画像
        meld_count : int
            自分の副露数
            
        Returns
        -------
        tuple
            (手牌エリア画像, ツモ牌画像) のタプル
        """
        # 副露数に応じて位置調整
        adjustment = self.hand_adjustment.get(meld_count, self.hand_adjustment[0])
        draw_adj = self.draw_tile_adjustment.get(meld_count, self.draw_tile_adjustment[0])
        
        # 基本座標（副露なしの場合の座標）
        base_x1, base_y1 = 210, 650
        
        # 調整後の座標
        x1 = base_x1 + adjustment["offset"]
        width = adjustment["width"]
        
        # 手牌エリアの切り出し
        hand_img = screen[base_y1:base_y1+70, x1:x1+width]
        
        # ツモ牌の切り出し
        draw_x, draw_y = draw_adj["x"], draw_adj["y"]
        draw_w, draw_h = draw_adj["width"], draw_adj["height"]
        draw_tile_img = screen[draw_y:draw_y+draw_h, draw_x:draw_x+draw_w]
        
        return hand_img, draw_tile_img
    
    def decode_melds_to_tiles(self, melds):
        """
        副露情報から牌のリストを取得する
        
        Parameters
        ----------
        melds : list
            副露情報のリスト
            
        Returns
        -------
        list
            副露牌の一覧
        """
        meld_tiles = []
        
        for meld in melds:
            meld_type = meld['type']
            tiles = meld['tiles']
            
            # 各副露タイプに応じた処理
            if meld_type == 'chi':
                # チーは順子（連続する3枚）
                meld_tiles.extend(tiles)
            elif meld_type == 'pon':
                # ポンは同じ牌3枚
                meld_tiles.extend(tiles)
            elif meld_type == 'kan' or meld_type == 'ankan' or meld_type == 'addon':
                # カンは同じ牌4枚
                meld_tiles.extend(tiles)
            
        return meld_tiles
    
    def get_meld_count(self, player_idx, player_melds):
        """
        指定プレイヤーの副露数を取得する
        
        Parameters
        ----------
        player_idx : int
            プレイヤーインデックス
        player_melds : list
            全プレイヤーの副露情報
            
        Returns
        -------
        int
            副露数
        """
        if player_idx < 0 or player_idx >= len(player_melds):
            return 0
        
        return len(player_melds[player_idx])
