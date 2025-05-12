#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀アシスタント初期設定ウィザード
"""

import os
import logging
import pygame
import numpy as np
from PIL import ImageGrab
from pygame.locals import *

logger = logging.getLogger("MahjongAssistant.UI.Setup")


class SetupWizard:
    """
    初期設定ウィザードクラス
    """
    
    def __init__(self, width=800, height=600):
        """
        初期化
        
        Parameters
        ----------
        width : int, optional
            ウィンドウの幅
        height : int, optional
            ウィンドウの高さ
        """
        # Pygameの初期化
        pygame.init()
        
        # ウィンドウサイズ
        self.width = width
        self.height = height
        
        # 画面の初期化
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("麻雀アシスタント - 初期設定")
        
        # 色設定
        self.bg_color = (41, 40, 45)  # 背景色
        self.text_color = (255, 247, 227)  # テキスト色
        self.highlight_color = (234, 183, 96)  # ハイライト色
        self.selection_color = (100, 120, 200, 128)  # 選択範囲色
        
        # フォント設定
        self.title_font = pygame.font.SysFont("notosanscjkjp", 28, bold=True)
        self.normal_font = pygame.font.SysFont("notosanscjkjp", 20)
        self.small_font = pygame.font.SysFont("notosanscjkjp", 16)
        
        # 設定項目
        self.items = [
            "手牌エリア",
            "ドラ表示エリア",
            "自分の河エリア",
            "右家の河エリア",
            "対面の河エリア",
            "左家の河エリア",
            "ターン表示エリア"
        ]
        
        # 領域設定（初期値）
        self.screen_areas = {
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
        
        # 現在設定中の項目インデックス
        self.current_item = 0
        
        # 選択中の領域
        self.selecting = False
        self.selection_start = None
        self.selection_end = None
        
        # スクリーンショット
        self.screenshot = None
        
        logger.info("SetupWizard初期化完了")
    
    def run(self):
        """
        ウィザードを実行
        
        Returns
        -------
        dict
            設定された領域情報
        """
        # メインループ
        running = True
        
        while running and self.current_item < len(self.items):
            # 画面更新
            self._update_screen()
            
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    # Enterキーで次の項目へ
                    elif event.key == pygame.K_RETURN:
                        self._next_item()
                    
                    # Sキーでスクリーンショット更新
                    elif event.key == pygame.K_s:
                        self._take_screenshot()
                        logger.info("スクリーンショット更新")
                    
                    # Bキーで前の項目へ戻る
                    elif event.key == pygame.K_b:
                        self._prev_item()
                
                # マウスイベント
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左クリック
                        # 選択開始
                        self.selecting = True
                        self.selection_start = event.pos
                        self.selection_end = event.pos
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.selecting:
                        # 選択範囲更新
                        self.selection_end = event.pos
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.selecting:
                        # 選択終了
                        self.selection_end = event.pos
                        self._set_current_area()
                        self.selecting = False
            
            # フレームレート制御
            pygame.time.delay(30)
        
        # 終了処理
        pygame.quit()
        
        logger.info("設定完了")
        return {
            'screen_areas': self.screen_areas
        }
    
    def _update_screen(self):
        """画面を更新"""
        # 背景
        self.screen.fill(self.bg_color)
        
        # スクリーンショットがあれば表示
        if self.screenshot is not None:
            # 縮小表示
            screenshot_height = int(self.screenshot.get_height() * 
                                   (self.width / self.screenshot.get_width()))
            screenshot_scaled = pygame.transform.scale(
                self.screenshot, (self.width, screenshot_height))
            
            self.screen.blit(screenshot_scaled, (0, 0))
        
        # 現在の設定項目
        self._draw_title(f"項目 {self.current_item+1}/{len(self.items)}: "
                        f"{self.items[self.current_item]}")
        
        # ガイドメッセージ
        self._draw_message("左クリックでドラッグして領域を選択してください。")
        self._draw_submessage("S: スクリーンショット更新 / Enter: 次へ / B: 戻る / ESC: キャンセル")
        
        # 選択中の領域を表示
        if self.selecting and self.selection_start is not None and self.selection_end is not None:
            x1, y1 = self.selection_start
            x2, y2 = self.selection_end
            
            # 座標を並べ替え（左上 -> 右下）
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # 選択範囲を描画
            selection_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            selection_surface.fill(self.selection_color)
            self.screen.blit(selection_surface, (left, top))
            
            # 枠線
            pygame.draw.rect(self.screen, self.highlight_color, 
                            (left, top, width, height), 2)
            
            # 座標表示
            pos_text = self.small_font.render(
                f"({left}, {top}, {left+width}, {top+height})", 
                True, self.highlight_color)
            self.screen.blit(pos_text, (left, top + height + 5))
        
        # 設定済み領域を表示
        self._draw_configured_areas()
        
        # 画面更新
        pygame.display.update()
    
    def _draw_title(self, text):
        """
        タイトルを描画
        
        Parameters
        ----------
        text : str
            タイトルテキスト
        """
        # 背景
        title_bg = pygame.Surface((self.width, 50))
        title_bg.fill((60, 59, 64))
        self.screen.blit(title_bg, (0, self.height - 100))
        
        # テキスト
        title = self.title_font.render(text, True, self.highlight_color)
        self.screen.blit(title, (self.width//2 - title.get_width()//2, self.height - 95))
    
    def _draw_message(self, text):
        """
        メッセージを描画
        
        Parameters
        ----------
        text : str
            メッセージテキスト
        """
        message = self.normal_font.render(text, True, self.text_color)
        self.screen.blit(message, (self.width//2 - message.get_width()//2, self.height - 50))
    
    def _draw_submessage(self, text):
        """
        サブメッセージを描画
        
        Parameters
        ----------
        text : str
            サブメッセージテキスト
        """
        message = self.small_font.render(text, True, self.text_color)
        self.screen.blit(message, (self.width//2 - message.get_width()//2, self.height - 25))
    
    def _draw_configured_areas(self):
        """設定済みの領域を表示"""
        # 他の設定済み領域を薄く表示
        areas = []
        
        # 手牌エリア
        if 'hand_area' in self.screen_areas:
            areas.append(('手牌', self.screen_areas['hand_area']))
        
        # ドラ表示エリア
        if 'dora_area' in self.screen_areas:
            areas.append(('ドラ', self.screen_areas['dora_area']))
        
        # 河エリア
        if 'river_areas' in self.screen_areas:
            river_names = ['自分', '右家', '対面', '左家']
            for i, area in enumerate(self.screen_areas['river_areas']):
                if i < len(river_names):
                    areas.append((f'河({river_names[i]})', area))
        
        # ターン表示エリア
        if 'turn_indicator_area' in self.screen_areas:
            areas.append(('ターン', self.screen_areas['turn_indicator_area']))
        
        # 設定済み領域を表示
        for name, area in areas:
            x1, y1, x2, y2 = area
            
            # 縮小表示の場合は座標を調整
            if self.screenshot is not None:
                scale_factor = self.width / self.screenshot.get_width()
                x1 = int(x1 * scale_factor)
                y1 = int(y1 * scale_factor)
                x2 = int(x2 * scale_factor)
                y2 = int(y2 * scale_factor)
            
            # 半透明の領域
            width = x2 - x1
            height = y2 - y1
            
            area_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            area_surface.fill((100, 100, 100, 80))
            self.screen.blit(area_surface, (x1, y1))
            
            # 枠線
            pygame.draw.rect(self.screen, (200, 200, 200), 
                            (x1, y1, width, height), 1)
            
            # 名前表示
            name_text = self.small_font.render(name, True, (200, 200, 200))
            self.screen.blit(name_text, (x1 + 5, y1 + 5))
    
    def _take_screenshot(self):
        """スクリーンショットを撮影"""
        try:
            # 画面全体をキャプチャ
            img = ImageGrab.grab()
            
            # PIL画像からPygame画像に変換
            mode = img.mode
            size = img.size
            data = img.tobytes()
            
            self.screenshot = pygame.image.fromstring(data, size, mode)
            logger.info(f"スクリーンショット撮影成功: {size}")
            
        except Exception as e:
            logger.error(f"スクリーンショット撮影中にエラー: {e}")
    
    def _set_current_area(self):
        """現在の選択範囲を設定に反映"""
        if self.selection_start is None or self.selection_end is None:
            return
        
        # 選択範囲の座標
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # 座標を並べ替え（左上 -> 右下）
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # スクリーンショットのスケールを考慮して実座標に変換
        if self.screenshot is not None:
            scale_factor = self.screenshot.get_width() / self.width
            left = int(left * scale_factor)
            top = int(top * scale_factor)
            right = int(right * scale_factor)
            bottom = int(bottom * scale_factor)
        
        # 項目に応じて設定
        if self.current_item == 0:
            # 手牌エリア
            self.screen_areas['hand_area'] = (left, top, right, bottom)
            logger.info(f"手牌エリア設定: {(left, top, right, bottom)}")
            
        elif self.current_item == 1:
            # ドラ表示エリア
            self.screen_areas['dora_area'] = (left, top, right, bottom)
            logger.info(f"ドラ表示エリア設定: {(left, top, right, bottom)}")
            
        elif 2 <= self.current_item <= 5:
            # 河エリア
            river_idx = self.current_item - 2
            if 'river_areas' not in self.screen_areas:
                self.screen_areas['river_areas'] = [None] * 4
                
            self.screen_areas['river_areas'][river_idx] = (left, top, right, bottom)
            logger.info(f"河エリア{river_idx}設定: {(left, top, right, bottom)}")
            
        elif self.current_item == 6:
            # ターン表示エリア
            self.screen_areas['turn_indicator_area'] = (left, top, right, bottom)
            logger.info(f"ターン表示エリア設定: {(left, top, right, bottom)}")
    
    def _next_item(self):
        """次の設定項目へ"""
        self.current_item = min(self.current_item + 1, len(self.items))
        
        # 最後まで設定したら終了
        if self.current_item >= len(self.items):
            logger.info("全項目の設定完了")
    
    def _prev_item(self):
        """前の設定項目へ"""
        self.current_item = max(self.current_item - 1, 0)
        logger.info(f"前の項目に戻る: {self.items[self.current_item]}")
