#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀牌認識モジュール - 雀魂(Mahjong Soul)向け
"""

import os
import logging
import cv2
import numpy as np
import tensorflow as tf
import time
import random
from PIL import ImageGrab

logger = logging.getLogger("MahjongAssistant.Recognizer")


class MahjongSoulRecognizer:
    """雀魂用牌認識クラス"""
    
    def __init__(self, screen_areas=None):
        """
        初期化
        
        Parameters
        ----------
        screen_areas : dict, optional
            画面領域の設定。Noneの場合はデフォルト値が使用される。
        """
        # デフォルトの画面領域設定
        default_areas = {
            'hand_area': (210, 650, 1070, 720),   # 手牌エリア
            'dora_area': (800, 300, 950, 350),    # ドラ表示エリア
            'river_areas': [
                (300, 450, 700, 580),   # 自分の河
                (750, 380, 900, 480),   # 右家の河
                (450, 150, 850, 250),   # 対面の河
                (150, 380, 300, 480)    # 左家の河
            ],
            'turn_indicator_area': (640, 360, 680, 400)  # ターン表示エリア
        }
        
        # 画面領域設定
        self.screen_areas = screen_areas if screen_areas else default_areas
        
        # 手牌エリア
        self.hand_area = self.screen_areas.get('hand_area', default_areas['hand_area'])
        # ドラ表示エリア
        self.dora_area = self.screen_areas.get('dora_area', default_areas['dora_area'])
        # 各プレイヤーの河エリア
        self.river_areas = self.screen_areas.get('river_areas', default_areas['river_areas'])
        # ターン表示エリア
        self.turn_indicator_area = self.screen_areas.get(
            'turn_indicator_area', default_areas['turn_indicator_area']
        )
        
        # 前回のデモデータ
        self.last_demo_data = None
        self.last_update_time = 0
        
        # 学習済みモデルのロード
        model_path = os.path.join(os.path.dirname(__file__), "../models/tile_recognition_model")
        if os.path.exists(model_path):
            try:
                self.model = tf.saved_model.load(model_path)
                logger.info("牌認識モデルを読み込みました")
            except Exception as e:
                logger.error(f"牌認識モデルのロードに失敗: {e}")
                self.model = None
        else:
            logger.warning("牌認識モデルが見つかりません。デモモードで動作します。")
            self.model = None
        
        # 雀魂特有の色彩情報を活用するためのカラーマスク設定
        self.tile_color_lower = np.array([20, 100, 100])  # 牌の色範囲（下限）HSV
        self.tile_color_upper = np.array([30, 255, 255])  # 牌の色範囲（上限）HSV
        
        logger.info("MahjongSoulRecognizer初期化完了")
    
    def detect_game_state(self):
        """
        ゲーム状態を検出
        
        Returns
        -------
        dict
            検出されたゲーム状態
        """
        # 画面全体をキャプチャ
        try:
            screen = np.array(ImageGrab.grab())
            logger.debug("画面キャプチャ成功")
        except Exception as e:
            logger.error(f"画面キャプチャに失敗: {e}")
            return self._empty_game_state()
        
        # 手牌エリアの切り出し
        hand_img = screen[self.hand_area[1]:self.hand_area[3], 
                          self.hand_area[0]:self.hand_area[2]]
        
        # ドラ表示エリアの切り出し
        dora_img = screen[self.dora_area[1]:self.dora_area[3], 
                          self.dora_area[0]:self.dora_area[2]]
        
        # 各プレイヤーの河エリアの切り出し
        river_imgs = []
        for area in self.river_areas:
            try:
                river_img = screen[area[1]:area[3], area[0]:area[2]]
                river_imgs.append(river_img)
            except:
                # 画面外の場合は黒画像を追加
                river_imgs.append(np.zeros((50, 150, 3), dtype=np.uint8))
        
        # リーチ棒検出（雀魂特有の視覚効果を利用）
        reach_indicators = self._detect_reach_indicators(screen)
        
        # 点数表示の読み取り
        scores = self._detect_scores(screen)
        
        # ターン表示の検出（誰の番か）
        current_player = self._detect_current_player(screen)
        
        logger.debug("ゲーム状態検出完了")
        return {
            'hand_img': hand_img,
            'dora_img': dora_img,
            'river_imgs': river_imgs,
            'reach_indicators': reach_indicators,
            'scores': scores,
            'current_player': current_player
        }
    
    def recognize_hand_tiles(self, hand_img):
        """
        手牌画像から牌を認識
        
        Parameters
        ----------
        hand_img : ndarray
            手牌エリアの画像
            
        Returns
        -------
        list
            認識された牌のリスト
        """
        if self.model is None:
            # デモモード: ランダムな手牌データを生成（30秒ごとに更新）
            current_time = time.time()
            if self.last_demo_data is None or current_time - self.last_update_time > 30:
                self.last_demo_data = self._generate_demo_hand_tiles()
                self.last_update_time = current_time
                logger.debug("デモ手牌データを更新しました")
            return self.last_demo_data
        
        # 実際の画像認識コード（モデルがある場合のみ実行）
        # HSV色空間に変換して牌の検出を容易に
        hsv = cv2.cvtColor(hand_img, cv2.COLOR_RGB2HSV)
        
        # 色マスクを適用して牌領域を強調
        mask = cv2.inRange(hsv, self.tile_color_lower, self.tile_color_upper)
        
        # 手牌の位置検出（雀魂ではほぼ等間隔配置）
        tile_positions = self._detect_tile_positions(mask)
        
        # 各牌位置から画像を切り出して認識
        hand_tiles = []
        for pos in tile_positions:
            x, y, w, h = pos
            tile_img = hand_img[y:y+h, x:x+w]
            # モデルで牌を識別
            tile_id = self._identify_tile(tile_img)
            hand_tiles.append(tile_id)
        
        logger.debug(f"認識した手牌: {len(hand_tiles)}枚")
        return hand_tiles
    
    def recognize_dora_indicators(self, dora_img):
        """
        ドラ表示画像からドラ表示牌を認識
        
        Parameters
        ----------
        dora_img : ndarray
            ドラ表示エリアの画像
            
        Returns
        -------
        list
            認識されたドラ表示牌のリスト
        """
        if self.model is None:
            # デモモード: ランダムなドラ表示牌
            # 現在の手牌データを基にランダムなドラを生成
            if hasattr(self, 'last_demo_data') and self.last_demo_data:
                # 手牌にないランダムな牌をドラにする
                all_tiles = list(range(0, 136, 4))  # 0, 4, 8, ...
                for tile in self.last_demo_data:
                    if tile in all_tiles:
                        all_tiles.remove(tile)
                return random.sample(all_tiles, min(2, len(all_tiles)))
            else:
                return [8, 20]  # デフォルト: 3萬, 6筒をドラと仮定
        
        # 処理は手牌認識と同様
        # ここでは簡略化のためにダミー実装
        return [8, 20]
    
    def recognize_river_tiles(self, river_img):
        """
        河画像から捨て牌を認識
        
        Parameters
        ----------
        river_img : ndarray
            河エリアの画像
            
        Returns
        -------
        list
            認識された捨て牌のリスト
        """
        if self.model is None:
            # デモモード: 河は毎回少しずつ変わるようにする
            river_size = random.randint(3, 6)  # 3〜6枚の捨て牌
            # 乱数シードを固定して毎回同じような結果を出すが、微妙に変化する
            random.seed(int(time.time() / 10))  # 10秒ごとに変化
            
            # 手牌と被らないようにする
            all_tiles = list(range(0, 136, 4))  # 0, 4, 8, ...
            if hasattr(self, 'last_demo_data') and self.last_demo_data:
                for tile in self.last_demo_data:
                    if tile in all_tiles:
                        all_tiles.remove(tile)
            
            return random.sample(all_tiles, min(river_size, len(all_tiles)))
        
        # 処理は手牌認識と同様
        # ここでは簡略化のためにダミー実装
        return [4, 16, 32, 40]
    
    def _detect_tile_positions(self, mask):
        """
        マスクから牌の位置を検出
        
        Parameters
        ----------
        mask : ndarray
            牌領域を示すマスク画像
            
        Returns
        -------
        list
            各牌の位置 (x, y, width, height) のリスト
        """
        # 輪郭検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 面積に基づくフィルタリング（牌のサイズ範囲内のみ）
        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 1000 < area < 3000:  # 雀魂の牌サイズに合わせて調整
                x, y, w, h = cv2.boundingRect(cnt)
                valid_contours.append((x, y, w, h))
        
        # x座標でソート（左から右へ）
        valid_contours.sort(key=lambda x: x[0])
        return valid_contours
    
    def _identify_tile(self, tile_img):
        """
        個別の牌画像を識別
        
        Parameters
        ----------
        tile_img : ndarray
            単一の牌画像
            
        Returns
        -------
        int
            識別された牌のID
        """
        if self.model is None:
            # デモモード: ランダムな牌IDを返す
            return np.random.randint(0, 34) * 4
        
        # 画像前処理
        try:
            resized = cv2.resize(tile_img, (64, 64))
            input_tensor = tf.convert_to_tensor(np.expand_dims(resized, 0))
            
            # モデルで推論
            predictions = self.model(input_tensor)
            class_id = np.argmax(predictions[0])
            
            # 雀魂特有の牌インデックスからゲーム内牌IDへの変換
            return self._ms_class_to_tile_id(class_id)
        except Exception as e:
            logger.error(f"牌識別処理でエラー: {e}")
            return 0  # エラー時は1萬を返す
    
    def _ms_class_to_tile_id(self, class_id):
        """
        雀魂の牌クラスからゲーム内牌IDへの変換
        
        Parameters
        ----------
        class_id : int
            モデルが識別した牌クラスID
            
        Returns
        -------
        int
            ゲーム内で使用する牌ID
        """
        # 雀魂特有のマッピング
        # 実際の実装では学習データに合わせて調整が必要
        ms_mapping = {
            # 萬子
            0: 0,   # 1萬
            1: 4,   # 2萬
            2: 8,   # 3萬
            3: 12,  # 4萬
            4: 16,  # 5萬
            5: 20,  # 6萬
            6: 24,  # 7萬
            7: 28,  # 8萬
            8: 32,  # 9萬
            
            # 筒子
            9: 36,   # 1筒
            10: 40,  # 2筒
            11: 44,  # 3筒
            12: 48,  # 4筒
            13: 52,  # 5筒
            14: 56,  # 6筒
            15: 60,  # 7筒
            16: 64,  # 8筒
            17: 68,  # 9筒
            
            # 索子
            18: 72,  # 1索
            19: 76,  # 2索
            20: 80,  # 3索
            21: 84,  # 4索
            22: 88,  # 5索
            23: 92,  # 6索
            24: 96,  # 7索
            25: 100, # 8索
            26: 104, # 9索
            
            # 字牌（風牌、三元牌）
            27: 108, # 東
            28: 112, # 南
            29: 116, # 西
            30: 120, # 北
            31: 124, # 白
            32: 128, # 發
            33: 132  # 中
        }
        return ms_mapping.get(class_id, 0)  # 未知のクラスIDの場合は1萬を返す
    
    def _detect_reach_indicators(self, screen):
        """
        リーチ棒の検出
        
        Parameters
        ----------
        screen : ndarray
            画面全体の画像
            
        Returns
        -------
        list
            各プレイヤーのリーチ状態 (True/False)
        """
        # デモモード: ランダムにリーチ状態を生成
        if self.model is None:
            # 10%の確率でリーチ状態を変更
            if not hasattr(self, 'demo_reach') or random.random() < 0.1:
                # 誰かがリーチしている確率は30%
                if random.random() < 0.3:
                    player = random.randint(0, 3)
                    self.demo_reach = [i == player for i in range(4)]
                else:
                    self.demo_reach = [False, False, False, False]
            return self.demo_reach
        
        # 実際の検出処理
        return [False, False, True, False]  # 対面がリーチと仮定
    
    def _detect_scores(self, screen):
        """
        点数表示の読み取り
        
        Parameters
        ----------
        screen : ndarray
            画面全体の画像
            
        Returns
        -------
        list
            各プレイヤーの点数
        """
        # デモモード: 適当な点数
        if self.model is None:
            if not hasattr(self, 'demo_scores'):
                # 初期点数は25000
                self.demo_scores = [25000, 25000, 25000, 25000]
            else:
                # 5%の確率で点数変動
                if random.random() < 0.05:
                    # 点棒移動（誰かが1000点失い、誰かが1000点得る）
                    loser = random.randint(0, 3)
                    winner = (loser + random.randint(1, 3)) % 4
                    self.demo_scores[loser] -= 1000
                    self.demo_scores[winner] += 1000
            return self.demo_scores
        
        # 実際の検出処理
        return [25000, 25000, 25000, 25000]
    
    def _detect_current_player(self, screen):
        """
        現在のターンプレイヤーを検出
        
        Parameters
        ----------
        screen : ndarray
            画面全体の画像
            
        Returns
        -------
        int
            現在の手番プレイヤーID（0:自分、1:右家、2:対面、3:左家）
        """
        # デモモード: ランダムに手番を変更（主に自分の番）
        if self.model is None:
            # 50%の確率で自分の番
            if random.random() < 0.5:
                return 0
            else:
                return random.randint(1, 3)
        
        # 実際の検出処理
        return 0  # 自分の番と仮定
    
    def _empty_game_state(self):
        """
        空のゲーム状態を作成
        
        Returns
        -------
        dict
            空のゲーム状態
        """
        return {
            'hand_img': np.zeros((70, 860, 3), dtype=np.uint8),
            'dora_img': np.zeros((50, 150, 3), dtype=np.uint8),
            'river_imgs': [np.zeros((130, 400, 3), dtype=np.uint8) for _ in range(4)],
            'reach_indicators': [False, False, False, False],
            'scores': [25000, 25000, 25000, 25000],
            'current_player': 0
        }
    
    def _generate_demo_hand_tiles(self):
        """
        デモ用の手牌データを生成（より麻雀らしい手牌）
        
        Returns
        -------
        list
            デモ用の手牌リスト
        """
        # 麻雀の牌山から13枚をランダムに選ぶ
        # 1枚4つあるので、tile_id * 4 とする（0, 4, 8, ...）
        
        # 種類ごとに選ぶ確率を調整
        tiles = []
        
        # 一定確率でメンツ（同じ数字3枚）を含める
        if random.random() < 0.7:  # 70%の確率でメンツを含める
            # メンツの基本牌を選ぶ
            base_tile = random.randint(0, 33)
            tiles.extend([base_tile * 4, base_tile * 4 + 1, base_tile * 4 + 2])
        
        # 一定確率で順子（連続する3枚）を含める
        if random.random() < 0.7:  # 70%の確率で順子を含める
            # 数牌から選ぶ（1-7スタート）
            suit = random.randint(0, 2)  # 0:萬子, 1:筒子, 2:索子
            start = random.randint(0, 6)  # 1-7
            
            base1 = suit * 9 + start
            base2 = suit * 9 + start + 1
            base3 = suit * 9 + start + 2
            
            tiles.extend([base1 * 4, base2 * 4, base3 * 4])
        
        # 一定確率で対子（同じ数字2枚）を含める
        if random.random() < 0.8:  # 80%の確率で対子を含める
            # 対子の基本牌を選ぶ
            base_tile = random.randint(0, 33)
            # すでに3枚使っている場合は別の牌を選ぶ
            count = tiles.count(base_tile * 4)
            while count >= 3:
                base_tile = random.randint(0, 33)
                count = tiles.count(base_tile * 4)
            
            tiles.extend([base_tile * 4, base_tile * 4 + 1])
        
        # 残りをランダムな牌で埋める
        all_tiles = []
        for i in range(34):  # 34種類
            all_tiles.extend([i * 4, i * 4 + 1, i * 4 + 2, i * 4 + 3])
        
        # すでに選ばれた牌を除外
        for tile in tiles:
            if tile in all_tiles:
                all_tiles.remove(tile)
        
        # 残りの枚数を選ぶ
        remaining = 13 - len(tiles)
        if remaining > 0:
            tiles.extend(random.sample(all_tiles, remaining))
        
        # 並べ替え
        tiles.sort()
        
        logger.debug(f"デモ手牌生成: {tiles}")
        return tiles
