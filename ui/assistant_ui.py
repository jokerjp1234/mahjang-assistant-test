#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀アシスタントUI - 雀魂(Mahjong Soul)向け
"""

import os
import logging
import pygame
import numpy as np
from pygame.locals import *

logger = logging.getLogger("MahjongAssistant.UI")


class MahjongSoulUI:
    """雀魂向けアシスタントUIクラス"""
    
    def __init__(self, width=350, height=600, is_demo_mode=False):
        """
        初期化
        
        Parameters
        ----------
        width : int, optional
            ウィンドウの幅
        height : int, optional
            ウィンドウの高さ
        is_demo_mode : bool, optional
            デモモードかどうか
        """
        # Pygameの初期化
        pygame.init()
        
        # ウィンドウサイズ
        self.width = width
        self.height = height
        
        # デモモードフラグ
        self.is_demo_mode = is_demo_mode
        
        # 画面の初期化
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.NOFRAME | pygame.SRCALPHA
        )
        pygame.display.set_caption("雀魂アシスタント")
        
        # 雀魂風の色彩設定
        self.bg_color = (41, 40, 45, 220)  # 雀魂の暗めの背景色
        self.text_color = (255, 247, 227)  # 雀魂のテキスト色
        self.highlight_color = (234, 183, 96)  # 雀魂の金色（ハイライト用）
        self.danger_color = (217, 79, 70)  # 赤色（危険牌用）
        self.demo_color = (255, 165, 0)  # オレンジ色（デモモード表示用）
        
        # フォント設定 - 日本語フォントの問題に対応
        self._setup_fonts()
        
        # 牌画像の読み込み
        self.tile_images = self._load_tile_images()
        
        # 背景画像読み込み
        self.bg_img = self._create_background()
        
        # パネル画像生成
        self.panel_img = self._create_panel()
        
        # ボタン画像生成
        self.button_img = self._create_button()
        
        # 現在表示されているゲーム状態
        self.current_display_state = {}
        
        logger.info("MahjongSoulUI初期化完了")
    
    def _setup_fonts(self):
        """日本語フォントの設定"""
        # 日本語フォント検索順序
        jp_font_names = [
            "Yu Gothic", "YuGothic",
            "MS Gothic", "MS PGothic", "MS Mincho", "MS PMincho",
            "Meiryo", "Meiryo UI",
            "Hiragino Sans", "Hiragino Kaku Gothic Pro",
            "Noto Sans CJK JP", "Noto Sans JP",
            "VL Gothic", "TakaoGothic", "IPAGothic", 
            "IPAPGothic", "IPAexGothic",
            "Droid Sans Japanese", "Droid Sans Fallback",
            # フォントファイル名（.ttfなし）
            "msgothic", "meiryo", "yumin", "yugothic", "ipagp"
        ]
        
        # システムフォントリスト取得
        system_fonts = pygame.font.get_fonts()
        logger.debug(f"システムフォント: {system_fonts[:10]}...")
        
        # 利用可能な日本語フォントを探す
        for font_name in jp_font_names:
            if font_name.lower() in system_fonts:
                self.font_name = font_name
                logger.info(f"日本語フォント: {font_name} を使用します")
                break
        else:
            # 見つからない場合はデフォルトフォントを使用
            self.font_name = pygame.font.get_default_font()
            logger.warning(f"日本語フォントが見つかりません。デフォルト({self.font_name})を使用します")
        
        try:
            self.title_font = pygame.font.SysFont(self.font_name, 28, bold=True)
            self.normal_font = pygame.font.SysFont(self.font_name, 20)
            self.small_font = pygame.font.SysFont(self.font_name, 16)
        except Exception as e:
            logger.error(f"フォント初期化エラー: {e}")
            # フォールバック - デフォルトフォント
            self.title_font = pygame.font.Font(None, 28)
            self.normal_font = pygame.font.Font(None, 20)
            self.small_font = pygame.font.Font(None, 16)
    
    def update(self, display_state):
        """
        UIを更新
        
        Parameters
        ----------
        display_state : dict
            表示データ（シャンテン数、最適捨て牌など）
        """
        # 現在の状態を保存
        self.current_display_state = display_state
        
        # 背景描画
        self.screen.blit(self.bg_img, (0, 0))
        
        # タイトルパネル
        self._draw_panel(10, 10, self.width - 20, 50)
        title = self.title_font.render("雀魂アシスタント", True, self.highlight_color)
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 20))
        
        # デモモード表示
        if self.is_demo_mode:
            demo_text = self.small_font.render("デモモード - 認識モデルなし", True, self.demo_color)
            self.screen.blit(demo_text, (self.width//2 - demo_text.get_width()//2, 45))
        
        # シャンテン数表示
        self._draw_panel(10, 70, self.width - 20, 50)
        shanten_text = self.normal_font.render(
            f"シャンテン数: {display_state.get('shanten', '?')}", True, self.text_color)
        self.screen.blit(shanten_text, (30, 80))
        
        # 推奨捨て牌
        self._draw_panel(10, 130, self.width - 20, 50)
        if display_state.get('best_discard') is not None:
            discard_text = self.normal_font.render("推奨捨て牌:", True, self.text_color)
            self.screen.blit(discard_text, (30, 140))
            self.screen.blit(
                self.tile_images.get(display_state['best_discard']//4, self.tile_images[0]), 
                (150, 135)
            )
        
        # 有効牌表示
        self._draw_panel(10, 190, self.width - 20, 90)
        eff_text = self.normal_font.render("有効牌:", True, self.text_color)
        self.screen.blit(eff_text, (30, 200))
        
        if 'effective_tiles' in display_state and display_state['effective_tiles']:
            for i, tile_id in enumerate(display_state['effective_tiles'][:7]):
                self.screen.blit(self.tile_images.get(tile_id, self.tile_images[0]), 
                                (30 + i*45, 230))
        
        # 危険牌表示
        self._draw_panel(10, 290, self.width - 20, 90)
        danger_text = self.normal_font.render("危険牌:", True, self.danger_color)
        self.screen.blit(danger_text, (30, 300))
        
        if 'dangers' in display_state and display_state['dangers']:
            danger_tiles = sorted(
                display_state['dangers'].items(), 
                key=lambda x: -x[1]
            )[:5]
            
            for i, (tile_id, danger) in enumerate(danger_tiles):
                if danger > 0.5:  # 危険度が一定以上の牌のみ表示
                    self.screen.blit(self.tile_images.get(tile_id, self.tile_images[0]), 
                                    (30 + i*45, 330))
                    # 危険度表示
                    d_level = self.small_font.render(
                        f"{danger:.1f}", True, self.danger_color)
                    self.screen.blit(d_level, (40 + i*45, 380))
        
        # 相手の待ち牌予測
        if 'opponent_waits' in display_state and display_state['opponent_waits']:
            self._draw_panel(10, 390, self.width - 20, 150)
            wait_text = self.normal_font.render(
                "待ち牌予測:", True, self.highlight_color)
            self.screen.blit(wait_text, (30, 400))
            
            y_pos = 430
            for player_id, waits in display_state['opponent_waits'].items():
                player_names = ["", "右家", "対面", "左家"]
                player_text = self.small_font.render(
                    f"{player_names[player_id]}:", True, self.text_color)
                self.screen.blit(player_text, (30, y_pos))
                
                for i, (tile_id, prob) in enumerate(
                    sorted(waits.items(), key=lambda x: -x[1])[:3]):
                    self.screen.blit(self.tile_images.get(tile_id, self.tile_images[0]), 
                                    (80 + i*50, y_pos-5))
                    # 確率表示
                    prob_text = self.small_font.render(
                        f"{prob*100:.0f}%", True, self.highlight_color)
                    self.screen.blit(prob_text, (85 + i*50, y_pos+35))
                
                y_pos += 60
        
        # デバッグ情報（画像認識されているかどうか）
        self._draw_panel(10, self.height - 60, self.width - 20, 50)
        if self.is_demo_mode:
            debug_text = self.small_font.render(
                "状態: モデルがロードされていません。認識されません。", True, self.demo_color)
        else:
            debug_text = self.small_font.render(
                "状態: 画像認識中", True, self.highlight_color)
        self.screen.blit(debug_text, (20, self.height - 45))
        
        # 画面更新
        pygame.display.update()
    
    def show_error(self, error_msg):
        """
        エラーメッセージを表示
        
        Parameters
        ----------
        error_msg : str
            エラーメッセージ
        """
        # エラーメッセージ用のパネル
        self._draw_panel(50, 200, self.width - 100, 150, (70, 30, 30, 220))
        
        # エラータイトル
        error_title = self.title_font.render("エラー", True, (255, 100, 100))
        self.screen.blit(error_title, (self.width//2 - error_title.get_width()//2, 220))
        
        # エラーメッセージ（複数行に分割）
        words = error_msg.split()
        lines = []
        current_line = words[0] if words else ""
        
        for word in words[1:]:
            if self.normal_font.size(current_line + " " + word)[0] < self.width - 120:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        
        for i, line in enumerate(lines[:3]):  # 最大3行まで
            text = self.normal_font.render(line, True, (255, 200, 200))
            self.screen.blit(text, (60, 260 + i * 30))
        
        # 閉じるボタン
        self._draw_button(self.width//2 - 40, 330, 80, 30, "閉じる")
        
        # 画面更新
        pygame.display.update()
    
    def quit(self):
        """終了処理"""
        pygame.quit()
    
    def _load_tile_images(self):
        """
        牌画像の読み込み
        
        Returns
        -------
        dict
            牌ID(34形式)をキーとする牌画像の辞書
        """
        # 牌画像のディレクトリ
        tile_dir = os.path.join(os.path.dirname(__file__), "../assets/tiles")
        
        # 牌画像辞書
        images = {}
        
        # ダミー画像（デバッグ用）
        dummy_img = pygame.Surface((40, 50))
        dummy_img.fill((150, 150, 150))
        
        # 牌タイプごとに画像読み込み
        for tile_type in range(34):
            # 牌の種類（0-8:萬子, 9-17:筒子, 18-26:索子, 27-33:字牌）
            if tile_type < 9:
                # 萬子
                tile_name = f"m{tile_type+1}.png"
            elif tile_type < 18:
                # 筒子
                tile_name = f"p{tile_type-8}.png"
            elif tile_type < 27:
                # 索子
                tile_name = f"s{tile_type-17}.png"
            else:
                # 字牌（東南西北白發中）
                z_names = ["east", "south", "west", "north", "white", "green", "red"]
                tile_name = f"z{z_names[tile_type-27]}.png"
            
            # 画像ファイルパス
            tile_path = os.path.join(tile_dir, tile_name)
            
            # 画像読み込み
            try:
                if os.path.exists(tile_path):
                    img = pygame.image.load(tile_path)
                    img = pygame.transform.scale(img, (40, 50))
                    images[tile_type] = img
                else:
                    # ファイルがなければダミー画像を使用
                    # タイル番号を描画
                    font = pygame.font.SysFont("Arial", 20)
                    text = font.render(str(tile_type), True, (0, 0, 0))
                    dummy = dummy_img.copy()
                    dummy.blit(text, (10, 15))
                    images[tile_type] = dummy
                    logger.warning(f"牌画像が見つかりません: {tile_path}")
            except Exception as e:
                logger.error(f"牌画像読み込みエラー: {e}")
                # エラー時はダミー画像を使用
                images[tile_type] = dummy_img
        
        return images
    
    def _create_background(self):
        """
        背景画像を作成
        
        Returns
        -------
        Surface
            背景画像
        """
        # 背景画像
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg.fill(self.bg_color)
        
        # 雀魂風の装飾（格子模様）
        for x in range(0, self.width, 20):
            pygame.draw.line(bg, (60, 59, 64, 100), (x, 0), (x, self.height), 1)
        
        for y in range(0, self.height, 20):
            pygame.draw.line(bg, (60, 59, 64, 100), (0, y), (self.width, y), 1)
        
        return bg
    
    def _create_panel(self):
        """
        パネル画像を作成
        
        Returns
        -------
        Surface
            パネル画像
        """
        # パネル画像（雀魂風の半透明パネル）
        panel = pygame.Surface((100, 100), pygame.SRCALPHA)
        panel.fill((60, 59, 64, 180))
        
        # 枠線
        pygame.draw.rect(panel, self.highlight_color, (0, 0, 100, 100), 2)
        
        return panel
    
    def _create_button(self):
        """
        ボタン画像を作成
        
        Returns
        -------
        Surface
            ボタン画像
        """
        # ボタン画像（雀魂風のボタン）
        button = pygame.Surface((100, 40), pygame.SRCALPHA)
        button.fill((80, 79, 84, 200))
        
        # 枠線
        pygame.draw.rect(button, self.highlight_color, (0, 0, 100, 40), 2)
        
        return button
    
    def _draw_panel(self, x, y, width, height, color=None):
        """
        パネルを描画
        
        Parameters
        ----------
        x : int
            X座標
        y : int
            Y座標
        width : int
            幅
        height : int
            高さ
        color : tuple, optional
            パネルの色
        """
        if color is None:
            color = (60, 59, 64, 180)
        
        # パネル
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill(color)
        
        # 枠線
        pygame.draw.rect(panel, self.highlight_color, (0, 0, width, height), 2)
        
        # 描画
        self.screen.blit(panel, (x, y))
    
    def _draw_button(self, x, y, width, height, text):
        """
        ボタンを描画
        
        Parameters
        ----------
        x : int
            X座標
        y : int
            Y座標
        width : int
            幅
        height : int
            高さ
        text : str
            ボタンテキスト
        """
        # ボタン
        button = pygame.Surface((width, height), pygame.SRCALPHA)
        button.fill((80, 79, 84, 200))
        
        # 枠線
        pygame.draw.rect(button, self.highlight_color, (0, 0, width, height), 2)
        
        # テキスト
        text_surface = self.small_font.render(text, True, self.text_color)
        button.blit(
            text_surface, 
            (width//2 - text_surface.get_width()//2, 
             height//2 - text_surface.get_height()//2)
        )
        
        # 描画
        self.screen.blit(button, (x, y))
