#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀アシスタントツール - メインプログラム

このプログラムは、雀魂（じゃんたま/Mahjong Soul）向けのリアルタイムアシスタントです。
画像認識技術を用いて画面から牌を読み取り、最適な戦略を提案します。
"""

import os
import sys
import time
import json
import argparse
import threading
import logging
import keyboard
import pygame
import numpy as np
import cv2
from pathlib import Path

# 自作モジュールのインポート
from recognizer.screen_capture import ScreenCapture
from recognizer.enhanced_recognizer import EnhancedMahjongRecognizer
from engine.mahjong_engine import MahjongEngine

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mahjong_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MahjongAssistant')


class MahjongAssistant:
    """麻雀アシスタントメインクラス"""
    
    def __init__(self, config_file=None):
        """
        初期化
        
        Parameters
        ----------
        config_file : str, optional
            設定ファイルのパス
        """
        # コンフィグの読み込み
        self.config = self._load_config(config_file)
        
        # 各モジュールの初期化
        self._init_modules()
        
        # UIの初期化
        self._init_ui()
        
        # 状態管理
        self.is_running = False
        self.is_visible = True
        self.last_update_time = 0
        self.update_interval = self.config.get('update_interval', 0.5)  # 更新間隔（秒）
        
        # ゲーム状態
        self.game_state = {
            'hand_tiles': [],
            'draw_tile': None,
            'dora_tiles': [],
            'discards': [],
            'melds': [],
            'shanten': -1,
            'suggestion': None
        }
        
        # スレッド
        self.recognition_thread = None
        
        logger.info('麻雀アシスタントが初期化されました')
    
    def _load_config(self, config_file):
        """
        設定ファイルを読み込む
        
        Parameters
        ----------
        config_file : str
            設定ファイルのパス
            
        Returns
        -------
        dict
            設定情報
        """
        default_config = {
            'hotkey': 'ctrl+alt+h',
            'update_interval': 0.5,
            'ui': {
                'width': 300,
                'height': 600,
                'position': (10, 10),
                'opacity': 0.8,
                'font_size': 16,
                'colors': {
                    'background': (0, 0, 0),
                    'text': (255, 255, 255),
                    'highlight': (255, 0, 0),
                    'good': (0, 255, 0),
                    'warning': (255, 255, 0),
                    'danger': (255, 0, 0)
                }
            }
        }
        
        # 設定ファイルがあれば読み込み
        config = default_config.copy()
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    # 設定をマージ
                    for key, value in loaded_config.items():
                        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                            config[key].update(value)
                        else:
                            config[key] = value
                            
                logger.info(f'設定ファイルを読み込みました: {config_file}')
            except Exception as e:
                logger.error(f'設定ファイルの読み込みに失敗しました: {e}')
        
        return config
    
    def _init_modules(self):
        """各モジュールを初期化する"""
        # 画面キャプチャモジュール
        self.screen_capture = ScreenCapture()
        
        # 設定ファイルの読み込み
        screen_config = 'screen_regions.cfg'
        if os.path.exists(screen_config):
            self.screen_capture.load_regions_config(screen_config)
        
        # 牌認識モジュール
        self.recognizer = EnhancedMahjongRecognizer()
        
        # 戦略エンジン
        self.engine = MahjongEngine()
        
        logger.info('各モジュールが初期化されました')
    
    def _init_ui(self):
        """UIを初期化する"""
        # Pygameの初期化
        pygame.init()
        pygame.display.set_caption('麻雀アシスタント')
        
        # UI設定の取得
        ui_config = self.config.get('ui', {})
        width = ui_config.get('width', 300)
        height = ui_config.get('height', 600)
        position = ui_config.get('position', (10, 10))
        opacity = ui_config.get('opacity', 0.8)
        
        # ウィンドウの作成
        self.screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
        
        # ウィンドウの位置設定
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{position[0]},{position[1]}"
        
        # フォントの設定
        font_size = ui_config.get('font_size', 16)
        self.font = pygame.font.SysFont('msgothic', font_size)
        self.font_large = pygame.font.SysFont('msgothic', font_size + 4)
        self.font_small = pygame.font.SysFont('msgothic', font_size - 2)
        
        # 色の設定
        colors = ui_config.get('colors', {})
        self.colors = {
            'background': colors.get('background', (0, 0, 0)),
            'text': colors.get('text', (255, 255, 255)),
            'highlight': colors.get('highlight', (255, 0, 0)),
            'good': colors.get('good', (0, 255, 0)),
            'warning': colors.get('warning', (255, 255, 0)),
            'danger': colors.get('danger', (255, 0, 0))
        }
        
        # ウィンドウの透明度設定
        self.screen.set_alpha(int(opacity * 255))
        
        # 牌画像の読み込み
        self.tile_images = self._load_tile_images()
        
        logger.info('UIが初期化されました')
    
    def _load_tile_images(self):
        """
        牌画像を読み込む
        
        Returns
        -------
        dict
            牌ID: 画像のマッピング
        """
        # 牌画像のディレクトリ
        tile_dir = Path('assets/tiles')
        
        # 牌画像が存在しない場合は空の辞書を返す
        if not tile_dir.exists():
            return {}
        
        # 牌IDのリスト
        tile_ids = [
            # 萬子
            'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9',
            # 筒子
            'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9',
            # 索子
            's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9',
            # 字牌
            'zeast', 'zsouth', 'zwest', 'znorth', 'zwhite', 'zgreen', 'zred'
        ]
        
        # 牌画像の読み込み
        tile_images = {}
        for tile_id in tile_ids:
            img_path = tile_dir / f'{tile_id}.png'
            
            if img_path.exists():
                try:
                    # Pygameで画像を読み込む
                    img = pygame.image.load(str(img_path))
                    
                    # サイズを調整（必要に応じて）
                    img = pygame.transform.scale(img, (30, 40))
                    
                    tile_images[tile_id] = img
                except Exception as e:
                    logger.error(f'牌画像の読み込みに失敗しました: {tile_id} - {e}')
        
        logger.info(f'{len(tile_images)}個の牌画像を読み込みました')
        return tile_images
    
    def start(self):
        """アシスタントを開始する"""
        self.is_running = True
        
        # 認識スレッドの開始
        self.recognition_thread = threading.Thread(target=self._recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        # ホットキーの設定
        hotkey = self.config.get('hotkey', 'ctrl+alt+h')
        keyboard.add_hotkey(hotkey, self._toggle_visibility)
        
        logger.info('麻雀アシスタントを開始しました')
        
        # メインループ
        self._main_loop()
    
    def _toggle_visibility(self):
        """表示/非表示を切り替える"""
        self.is_visible = not self.is_visible
        logger.info(f'表示状態を切り替えました: {"表示" if self.is_visible else "非表示"}')
    
    def _recognition_loop(self):
        """牌認識のループ処理"""
        logger.info('牌認識スレッドを開始しました')
        
        while self.is_running:
            try:
                # 更新間隔の制御
                current_time = time.time()
                if current_time - self.last_update_time < self.update_interval:
                    time.sleep(0.1)
                    continue
                
                # 画面キャプチャ
                captures = self.screen_capture.capture_all_regions()
                
                # 牌認識
                hand_img = captures.get('hand')
                dora_img = captures.get('dora')
                melds_img = captures.get('melds')
                
                # ゲーム状態の検出
                self.recognizer.detect_game_state()
                
                # 手牌の認識
                hand_tiles = self.recognizer.recognize_hand_tiles(hand_img)
                
                # ツモ牌の認識
                draw_tile = self.recognizer.recognize_draw_tile()
                
                # ドラの認識
                dora_tiles = self.recognizer.recognize_dora_indicators(dora_img)
                
                # 副露の認識
                meld_tiles = self.recognizer.recognize_meld_tiles(0)  # 自分の副露
                
                # 戦略エンジンに情報を渡す
                self.engine.set_hand(hand_tiles)
                self.engine.set_melds(meld_tiles)
                self.engine.set_dora(dora_tiles)
                
                # シャンテン数の計算
                shanten = self.engine.calculate_shanten()
                
                # 捨て牌の提案
                suggestion = self.engine.suggest_discard()
                
                # ゲーム状態の更新
                self.game_state.update({
                    'hand_tiles': hand_tiles,
                    'draw_tile': draw_tile,
                    'dora_tiles': dora_tiles,
                    'melds': meld_tiles,
                    'shanten': shanten,
                    'suggestion': suggestion
                })
                
                self.last_update_time = current_time
                
            except Exception as e:
                logger.error(f'牌認識処理中にエラーが発生しました: {e}')
                time.sleep(1)
    
    def _main_loop(self):
        """メインループ処理"""
        try:
            clock = pygame.time.Clock()
            
            while self.is_running:
                # イベント処理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.is_running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.is_running = False
                
                # 表示状態に応じて描画
                if self.is_visible:
                    self._render_ui()
                else:
                    # 非表示時は最小サイズのウィンドウにする
                    self.screen.fill((0, 0, 0, 0))
                
                pygame.display.update()
                clock.tick(30)
                
        except KeyboardInterrupt:
            logger.info('ユーザーによって終了が要求されました')
        except Exception as e:
            logger.error(f'メインループ中にエラーが発生しました: {e}')
        finally:
            self._cleanup()
    
    def _render_ui(self):
        """UIを描画する"""
        # 背景の描画
        self.screen.fill(self.colors['background'])
        
        # タイトルの描画
        title = self.font_large.render('麻雀アシスタント', True, self.colors['highlight'])
        self.screen.blit(title, (10, 10))
        
        # シャンテン数の表示
        shanten = self.game_state['shanten']
        if shanten == -1:
            shanten_text = "和了"
            shanten_color = self.colors['good']
        elif shanten == 0:
            shanten_text = "テンパイ"
            shanten_color = self.colors['good']
        else:
            shanten_text = f"{shanten}向聴"
            shanten_color = self.colors['text']
        
        shanten_surface = self.font.render(f'シャンテン数: {shanten_text}', True, shanten_color)
        self.screen.blit(shanten_surface, (10, 50))
        
        # 手牌の表示
        self._render_hand_tiles()
        
        # 捨て牌提案の表示
        self._render_suggestion()
        
        # 有効牌の表示
        self._render_effective_tiles()
        
        # 副露の表示
        self._render_melds()
        
        # ドラの表示
        self._render_dora()
        
        # 操作ガイドの表示
        guide_text = '表示/非表示: ' + self.config.get('hotkey', 'Ctrl+Alt+H')
        guide_surface = self.font_small.render(guide_text, True, self.colors['text'])
        
        height = self.screen.get_height()
        self.screen.blit(guide_surface, (10, height - 30))
    
    def _render_hand_tiles(self):
        """手牌を描画する"""
        hand_tiles = self.game_state['hand_tiles']
        draw_tile = self.game_state['draw_tile']
        
        if not hand_tiles:
            text = self.font.render('手牌を認識できません', True, self.colors['warning'])
            self.screen.blit(text, (10, 80))
            return
        
        # 手牌の描画
        y_pos = 80
        x_pos = 10
        
        # 手牌の描画（画像またはテキスト）
        for i, tile in enumerate(sorted(hand_tiles)):
            if tile in self.tile_images:
                # 画像での描画
                self.screen.blit(self.tile_images[tile], (x_pos, y_pos))
                x_pos += 32  # 画像の幅+間隔
            else:
                # テキストでの描画
                tile_name = self.engine.get_tile_name(tile)
                text = self.font_small.render(tile_name, True, self.colors['text'])
                self.screen.blit(text, (x_pos, y_pos))
                x_pos += 30  # テキストの幅+間隔
        
        # ツモ牌の描画（あれば）
        if draw_tile:
            # 区切り線
            pygame.draw.line(self.screen, self.colors['text'], 
                             (x_pos, y_pos + 10), (x_pos, y_pos + 30), 2)
            x_pos += 10
            
            if draw_tile in self.tile_images:
                self.screen.blit(self.tile_images[draw_tile], (x_pos, y_pos))
            else:
                tile_name = self.engine.get_tile_name(draw_tile)
                text = self.font_small.render(tile_name, True, self.colors['good'])
                self.screen.blit(text, (x_pos, y_pos))
    
    def _render_suggestion(self):
        """捨て牌提案を描画する"""
        suggestion = self.game_state['suggestion']
        
        if not suggestion or not suggestion['discard']:
            return
        
        y_pos = 140
        
        # 提案タイトル
        title = self.font.render('捨て牌提案:', True, self.colors['highlight'])
        self.screen.blit(title, (10, y_pos))
        y_pos += 30
        
        # 捨て牌の描画
        discard = suggestion['discard']
        reason = suggestion['reason']
        
        if discard in self.tile_images:
            self.screen.blit(self.tile_images[discard], (20, y_pos))
            x_offset = 60
        else:
            tile_name = self.engine.get_tile_name(discard)
            x_offset = 20
        
        # 捨て牌名と理由
        tile_name = self.engine.get_tile_name(discard)
        text = self.font.render(f'{tile_name} - {reason}', True, self.colors['good'])
        self.screen.blit(text, (x_offset, y_pos))
    
    def _render_effective_tiles(self):
        """有効牌を描画する"""
        suggestion = self.game_state['suggestion']
        
        if not suggestion or not suggestion.get('effective_tiles'):
            return
        
        effective_tiles = suggestion['effective_tiles']
        
        y_pos = 180
        
        # 有効牌タイトル
        title = self.font.render('有効牌:', True, self.colors['highlight'])
        self.screen.blit(title, (10, y_pos))
        y_pos += 30
        
        # 有効牌の描画
        x_pos = 20
        count = 0
        
        for tile, improvement in effective_tiles.items():
            if tile in self.tile_images:
                # 画像での描画
                self.screen.blit(self.tile_images[tile], (x_pos, y_pos))
                x_pos += 32  # 画像の幅+間隔
            else:
                # テキストでの描画
                tile_name = self.engine.get_tile_name(tile)
                text = self.font_small.render(tile_name, True, self.colors['text'])
                self.screen.blit(text, (x_pos, y_pos))
                x_pos += 40  # テキストの幅+間隔
            
            count += 1
            if count >= 8:  # 1行に表示する最大数
                count = 0
                x_pos = 20
                y_pos += 45  # 次の行へ
    
    def _render_melds(self):
        """副露を描画する"""
        melds = self.game_state['melds']
        
        if not melds:
            return
        
        y_pos = 280
        
        # 副露タイトル
        title = self.font.render('副露:', True, self.colors['highlight'])
        self.screen.blit(title, (10, y_pos))
        y_pos += 30
        
        # 副露の描画
        x_pos = 20
        
        for tile in melds:
            if tile in self.tile_images:
                self.screen.blit(self.tile_images[tile], (x_pos, y_pos))
                x_pos += 32
            else:
                tile_name = self.engine.get_tile_name(tile)
                text = self.font_small.render(tile_name, True, self.colors['text'])
                self.screen.blit(text, (x_pos, y_pos))
                x_pos += 40
    
    def _render_dora(self):
        """ドラを描画する"""
        dora_tiles = self.game_state['dora_tiles']
        
        if not dora_tiles:
            return
        
        y_pos = 340
        
        # ドラタイトル
        title = self.font.render('ドラ表示牌:', True, self.colors['highlight'])
        self.screen.blit(title, (10, y_pos))
        y_pos += 30
        
        # ドラの描画
        x_pos = 20
        
        for tile in dora_tiles:
            if tile in self.tile_images:
                self.screen.blit(self.tile_images[tile], (x_pos, y_pos))
                x_pos += 32
            else:
                tile_name = self.engine.get_tile_name(tile)
                text = self.font_small.render(tile_name, True, self.colors['text'])
                self.screen.blit(text, (x_pos, y_pos))
                x_pos += 40
    
    def _cleanup(self):
        """終了処理"""
        # Pygameの終了
        pygame.quit()
        
        # キーボードフックの解除
        keyboard.unhook_all()
        
        logger.info('麻雀アシスタントを終了しました')


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='麻雀アシスタントツール')
    parser.add_argument('--config', type=str, default='config.json', help='設定ファイルのパス')
    parser.add_argument('--setup', action='store_true', help='画面領域設定ウィザードを起動')
    
    args = parser.parse_args()
    
    # 画面領域設定ウィザード
    if args.setup:
        screen_capture = ScreenCapture()
        screen_capture.setup_regions_interactive()
        return
    
    # 麻雀アシスタントの起動
    assistant = MahjongAssistant(args.config)
    assistant.start()


if __name__ == "__main__":
    main()
