#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀アシスタント初期設定ウィザード - 改良版
雀魂画面上で直接範囲を指定できる完全透明オーバーレイ型設定画面
"""

import os
import logging
import pygame
import numpy as np
import keyboard
from PIL import ImageGrab
from pygame.locals import *

logger = logging.getLogger("MahjongAssistant.UI.Setup")


class SetupWizard:
    """
    初期設定ウィザードクラス（完全透明オーバーレイ型）
    """
    
    def __init__(self):
        """初期化"""
        # Pygameの初期化
        pygame.init()
        
        # 画面サイズ（スクリーン全体）
        screen_info = pygame.display.Info()
        self.width = screen_info.current_w
        self.height = screen_info.current_h
        
        # 画面の初期化（完全透明オーバーレイ）
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.NOFRAME | pygame.SRCALPHA
        )
        pygame.display.set_caption("麻雀アシスタント - 設定ウィザード")
        
        # 色設定
        self.bg_color = (0, 0, 0, 0)  # 完全透明
        self.text_color = (255, 255, 255)  # テキスト色
        self.highlight_color = (234, 183, 96)  # ハイライト色
        self.selection_color = (100, 200, 255, 60)  # 選択範囲色（より透明）
        self.completed_selection_color = (100, 255, 100, 40)  # 完了選択色（より透明）
        self.configured_area_color = (100, 100, 100, 30)  # 設定済み領域（より透明）
        
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
        
        # マウスカーソル位置
        self.mouse_pos = (0, 0)
        
        # 選択完了したかどうか
        self.selection_completed = False
        
        # 説明パネルの位置とトグル
        self.panel_x = 20
        self.panel_y = 20
        self.panel_width = 300
        self.panel_height = 150
        self.show_panel = True  # パネル表示トグル
        
        # マウス位置表示トグル
        self.show_mouse_pos = True
        
        # 制御キー情報
        self.control_keys = [
            {"key": "Enter", "desc": "次の項目へ"},
            {"key": "Esc", "desc": "キャンセル"},
            {"key": "B", "desc": "前の項目へ"},
            {"key": "C", "desc": "設定を完了"},
            {"key": "H", "desc": "ヘルプパネル表示/非表示"},
            {"key": "M", "desc": "マウス座標表示/非表示"}
        ]
        
        # キーボードフックの設定
        self._setup_keyboard_hooks()
        
        logger.info("SetupWizard初期化完了")
    
    def _setup_keyboard_hooks(self):
        """キーボードのグローバルフックを設定"""
        # Enterキーで次の項目へ
        keyboard.add_hotkey('enter', self._next_item)
        
        # Bキーで前の項目へ
        keyboard.add_hotkey('b', self._prev_item)
        
        # Cキーで設定完了
        keyboard.add_hotkey('c', self._complete_setup)
        
        # Hキーでヘルプパネル表示/非表示
        keyboard.add_hotkey('h', self._toggle_panel)
        
        # Mキーでマウス位置表示/非表示
        keyboard.add_hotkey('m', self._toggle_mouse_pos)
    
    def _toggle_panel(self):
        """ヘルプパネル表示/非表示を切り替え"""
        self.show_panel = not self.show_panel
        logger.info(f"ヘルプパネル表示: {self.show_panel}")
    
    def _toggle_mouse_pos(self):
        """マウス位置表示/非表示を切り替え"""
        self.show_mouse_pos = not self.show_mouse_pos
        logger.info(f"マウス位置表示: {self.show_mouse_pos}")
    
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
        
        while running:
            # 画面更新
            self._update_screen()
            
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                # マウスの位置を常に取得
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_pos = event.pos
                
                # マウスイベント
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左クリック
                        # 選択開始
                        self.selecting = True
                        self.selection_start = event.pos
                        self.selection_end = event.pos
                        self.selection_completed = False
                
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
                        self.selection_completed = True
            
            # 設定が完了したら終了
            if self.current_item >= len(self.items):
                running = False
            
            # フレームレート制御
            pygame.time.delay(30)
        
        # キーボードフックの解除
        keyboard.unhook_all()
        
        # 終了処理
        pygame.quit()
        
        logger.info("設定完了")
        return {
            'screen_areas': self.screen_areas
        }
    
    def _update_screen(self):
        """画面を更新"""
        # 透明な背景
        self.screen.fill(self.bg_color)
        
        # 設定済み領域を表示（最も透明度を低く）
        self._draw_configured_areas()
        
        # 選択完了した領域を表示
        if self.selection_completed:
            self._draw_completed_selection()
        
        # 選択中の領域を表示（最前面）
        if self.selecting and self.selection_start is not None and self.selection_end is not None:
            self._draw_selection()
        
        # 情報パネル（トグル可能）
        if self.show_panel:
            self._draw_info_panel()
        
        # マウス位置を表示（トグル可能）
        if self.show_mouse_pos:
            self._draw_mouse_position()
        
        # 画面更新
        pygame.display.update()
    
    def _draw_selection(self):
        """選択中の領域を描画"""
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # 座標を並べ替え（左上 -> 右下）
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # 選択範囲を描画（より透明）
        selection_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        selection_surface.fill(self.selection_color)
        self.screen.blit(selection_surface, (left, top))
        
        # 枠線（細めに）
        pygame.draw.rect(self.screen, self.highlight_color, 
                        (left, top, width, height), 1)
        
        # 座標表示（シンプルに）
        pos_text = self.small_font.render(
            f"({left}, {top}, {left+width}, {top+height})", 
            True, self.highlight_color)
        
        # 座標表示の背景（よりコンパクトで透明に）
        text_width, text_height = pos_text.get_size()
        text_bg = pygame.Surface((text_width + 10, text_height + 4), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 80))  # 背景をより透明に
        
        # 画面の下部に表示して邪魔にならないように
        self.screen.blit(text_bg, (left, top + height + 5))
        self.screen.blit(pos_text, (left + 5, top + height + 7))
    
    def _draw_completed_selection(self):
        """選択完了した領域を描画"""
        if self.current_item == 0:
            # 手牌エリア
            area = self.screen_areas['hand_area']
        elif self.current_item == 1:
            # ドラ表示エリア
            area = self.screen_areas['dora_area']
        elif 2 <= self.current_item <= 5:
            # 河エリア
            river_idx = self.current_item - 2
            if 'river_areas' in self.screen_areas and len(self.screen_areas['river_areas']) > river_idx:
                area = self.screen_areas['river_areas'][river_idx]
            else:
                return
        elif self.current_item == 6:
            # ターン表示エリア
            area = self.screen_areas['turn_indicator_area']
        else:
            return
        
        left, top, right, bottom = area
        width = right - left
        height = bottom - top
        
        # 選択範囲を描画（よりシンプルで透明に）
        selection_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        selection_surface.fill(self.completed_selection_color)
        self.screen.blit(selection_surface, (left, top))
        
        # 枠線（より薄く）
        pygame.draw.rect(self.screen, (0, 255, 0, 128), 
                        (left, top, width, height), 1)
    
    def _draw_configured_areas(self):
        """設定済みの領域を表示（より透明に）"""
        # 他の設定済み領域を薄く表示
        areas = []
        
        # 手牌エリア
        if 'hand_area' in self.screen_areas and self.current_item != 0:
            areas.append(('手牌', self.screen_areas['hand_area']))
        
        # ドラ表示エリア
        if 'dora_area' in self.screen_areas and self.current_item != 1:
            areas.append(('ドラ', self.screen_areas['dora_area']))
        
        # 河エリア
        if 'river_areas' in self.screen_areas:
            river_names = ['自分', '右家', '対面', '左家']
            for i, area in enumerate(self.screen_areas['river_areas']):
                if i < len(river_names) and self.current_item != i + 2:
                    areas.append((f'河({river_names[i]})', area))
        
        # ターン表示エリア
        if 'turn_indicator_area' in self.screen_areas and self.current_item != 6:
            areas.append(('ターン', self.screen_areas['turn_indicator_area']))
        
        # 設定済み領域を表示
        for name, area in areas:
            x1, y1, x2, y2 = area
            
            # 非常に透明な領域
            width = x2 - x1
            height = y2 - y1
            
            area_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            area_surface.fill(self.configured_area_color)
            self.screen.blit(area_surface, (x1, y1))
            
            # 細い枠線
            pygame.draw.rect(self.screen, (200, 200, 200, 100), 
                            (x1, y1, width, height), 1)
            
            # 必要な時だけ名前表示
            if self.show_panel:
                name_text = self.small_font.render(name, True, (200, 200, 200, 150))
                self.screen.blit(name_text, (x1 + 5, y1 + 5))
    
    def _draw_info_panel(self):
        """情報パネルを描画（より透明に）"""
        # パネル背景
        panel = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))  # より透明に
        
        # 枠線（細めに）
        pygame.draw.rect(panel, self.highlight_color, 
                        (0, 0, self.panel_width, self.panel_height), 1)
        
        # タイトル
        title = self.title_font.render(
            f"設定中: {self.items[self.current_item]}", True, self.highlight_color)
        panel.blit(title, (10, 10))
        
        # 説明
        desc = self.normal_font.render(
            "範囲を選択してください", True, self.text_color)
        panel.blit(desc, (10, 45))
        
        # キー説明
        y_offset = 75
        for key_info in self.control_keys:
            key_text = self.small_font.render(
                f"{key_info['key']}: {key_info['desc']}", True, self.text_color)
            panel.blit(key_text, (10, y_offset))
            y_offset += 20
        
        # パネルを画面に描画
        self.screen.blit(panel, (self.panel_x, self.panel_y))
    
    def _draw_mouse_position(self):
        """マウス位置を表示（よりシンプルに）"""
        x, y = self.mouse_pos
        pos_text = self.small_font.render(f"X: {x}, Y: {y}", True, (255, 255, 255))
        
        # 背景付きで表示（読みやすくするため、より透明に）
        text_width, text_height = pos_text.get_size()
        text_bg = pygame.Surface((text_width + 10, text_height + 4), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 80))  # 背景をより透明に
        
        # 右下に表示して邪魔にならないように
        pos_x = self.width - text_width - 30
        pos_y = self.height - text_height - 20
        
        self.screen.blit(text_bg, (pos_x - 5, pos_y - 2))
        self.screen.blit(pos_text, (pos_x, pos_y))
    
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
        # 現在の項目が設定済みかチェック
        if not self.selection_completed:
            logger.warning(f"項目 {self.items[self.current_item]} は未設定です")
            return
        
        self.current_item = min(self.current_item + 1, len(self.items))
        self.selection_completed = False
        
        # 最後まで設定したら終了
        if self.current_item >= len(self.items):
            logger.info("全項目の設定完了")
        else:
            logger.info(f"次の項目: {self.items[self.current_item]}")
    
    def _prev_item(self):
        """前の設定項目へ"""
        self.current_item = max(self.current_item - 1, 0)
        
        # 前の項目の選択状態を復元
        self.selection_completed = True
        
        logger.info(f"前の項目に戻る: {self.items[self.current_item]}")
    
    def _complete_setup(self):
        """設定を完了する"""
        # すべての項目が設定されているか確認
        all_set = True
        
        if 'hand_area' not in self.screen_areas:
            all_set = False
        
        if 'dora_area' not in self.screen_areas:
            all_set = False
        
        if 'river_areas' not in self.screen_areas or len(self.screen_areas['river_areas']) < 4:
            all_set = False
        
        if 'turn_indicator_area' not in self.screen_areas:
            all_set = False
        
        if all_set:
            # 設定完了
            self.current_item = len(self.items)
            logger.info("設定が完了しました")
        else:
            logger.warning("すべての項目が設定されていません")
