#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
麻雀アシスタントツール - メインプログラム
"""

import os
import sys
import time
import json
import logging
import argparse
import traceback
import keyboard
import pygame
from pygame.locals import *

# モジュールパスの設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 自作モジュールのインポート
from recognizer.tile_recognizer import MahjongSoulRecognizer
from engine.mahjong_engine import MahjongSoulEngine
from ui.assistant_ui import MahjongSoulUI
from ui.setup_wizard import SetupWizard

# 設定ファイルパス
CONFIG_FILE = os.path.join(current_dir, "config.json")

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mahjong_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MahjongAssistant")

# グローバル変数
running = True
visible = True
ui = None


def toggle_visibility():
    """アシスタント表示/非表示切替"""
    global visible
    visible = not visible
    logger.info(f"アシスタント表示状態: {visible}")
    if not visible:
        # 非表示時は画面を最小化
        pygame.display.iconify()
    else:
        # 表示時は画面を前面に
        pygame.display.flip()


def quit_app():
    """アプリケーション終了"""
    global running
    logger.info("アプリケーション終了")
    running = False


def save_config(config):
    """設定をファイルに保存する"""
    try:
        # screen_areasの内部リストをJSON互換に変換
        json_config = {
            'screen_areas': {}
        }
        
        # 通常の値（タプル→リスト変換）
        for key, value in config['screen_areas'].items():
            if key != 'river_areas':
                json_config['screen_areas'][key] = list(value)
            else:
                # リストの中のタプル変換
                json_config['screen_areas'][key] = [list(item) for item in value]
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_config, f, indent=4, ensure_ascii=False)
        logger.info(f"設定を保存しました: {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"設定の保存に失敗しました: {e}")
        return False


def load_config():
    """保存された設定を読み込む"""
    if not os.path.exists(CONFIG_FILE):
        logger.info("設定ファイルが見つかりません")
        return {}
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            json_config = json.load(f)
        
        # JSON形式からタプルに変換（リスト→タプル）
        config = {
            'screen_areas': {}
        }
        
        # 通常の値（リスト→タプル変換）
        for key, value in json_config['screen_areas'].items():
            if key != 'river_areas':
                config['screen_areas'][key] = tuple(value)
            else:
                # リストの中のリスト変換
                config['screen_areas'][key] = [tuple(item) for item in value]
        
        logger.info(f"設定を読み込みました: {CONFIG_FILE}")
        return config
    except Exception as e:
        logger.error(f"設定の読み込みに失敗しました: {e}")
        return {}


def main():
    """麻雀アシスタントのメイン処理"""
    global running, visible, ui
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='麻雀アシスタントツール')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで実行')
    parser.add_argument('--no-setup', action='store_true', help='初期設定ウィザードをスキップ')
    parser.add_argument('--reset-config', action='store_true', help='設定をリセットして初期設定を実行')
    args = parser.parse_args()
    
    # デバッグモード設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("デバッグモードで起動")
    
    try:
        # 設定の読み込み
        config = load_config()
        
        # 初期設定ウィザード（画面領域の設定など）
        if args.reset_config or not config or not args.no_setup:
            setup_wizard = SetupWizard()
            if config and 'screen_areas' in config:
                # 既存の設定があれば初期値として渡す
                setup_wizard.screen_areas = config['screen_areas']
            
            config = setup_wizard.run()
            
            # 設定を保存
            save_config(config)
            logger.info("初期設定完了・保存")
        else:
            logger.info("保存された設定を使用します")
        
        # コンポーネント初期化
        recognizer = MahjongSoulRecognizer(config.get('screen_areas', {}))
        engine = MahjongSoulEngine()
        ui = MahjongSoulUI()
        logger.info("コンポーネント初期化完了")
        
        # ホットキー設定
        keyboard.add_hotkey('ctrl+alt+h', toggle_visibility)  # 表示/非表示切替
        keyboard.add_hotkey('ctrl+alt+q', quit_app)  # 終了
        logger.info("ホットキー設定完了")
        
        # メインループ
        pygame.display.set_caption("雀魂アシスタント")
        clock = pygame.time.Clock()
        logger.info("メインループ開始")
        
        while running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            if visible:
                try:
                    # ゲーム状態検出
                    captured_state = recognizer.detect_game_state()
                    
                    # 手牌認識
                    hand_tiles = recognizer.recognize_hand_tiles(captured_state['hand_img'])
                    logger.debug(f"認識された手牌: {hand_tiles}")
                    
                    # ドラ認識
                    dora_tiles = recognizer.recognize_dora_indicators(captured_state['dora_img'])
                    
                    # 各プレイヤーの河認識
                    river_tiles = [
                        recognizer.recognize_river_tiles(img) 
                        for img in captured_state['river_imgs']
                    ]
                    
                    # ゲーム状態構築
                    game_state = {
                        'hand': hand_tiles,
                        'dora': dora_tiles,
                        'rivers': river_tiles,
                        'scores': captured_state['scores'],
                        'reach_status': captured_state['reach_indicators'],
                        'current_player': captured_state['current_player']
                    }
                    
                    # 戦略計算
                    # シャンテン数計算
                    shanten = engine.calculate_shanten(hand_tiles)
                    
                    # 最適な捨て牌
                    best_discard, _ = engine.calculate_best_discard(
                        hand_tiles, dora_tiles, 
                        [t for river in river_tiles for t in river]
                    )
                    
                    # 有効牌計算
                    effective_tiles = engine.calculate_effective_tiles(hand_tiles)
                    
                    # 危険牌計算
                    dangers = {
                        tile//4: engine.calculate_danger(
                            tile, [t for river in river_tiles for t in river],
                            game_state['reach_status']
                        ) for tile in hand_tiles
                    }
                    
                    # 相手の待ち牌予測
                    opponent_waits = {}
                    for i, reach in enumerate(game_state['reach_status']):
                        if reach and i > 0:  # 相手がリーチしている場合
                            opponent_waits[i] = engine.predict_opponent_waits(
                                river_tiles[i], [], True
                            )
                    
                    # 表示用データ構築
                    display_state = {
                        'shanten': shanten,
                        'best_discard': best_discard,
                        'effective_tiles': effective_tiles,
                        'dangers': dangers,
                        'opponent_waits': opponent_waits
                    }
                    
                    # UI更新
                    ui.update(display_state)
                    
                except Exception as e:
                    logger.error(f"処理中にエラーが発生: {e}")
                    logger.debug(traceback.format_exc())
                    # エラー表示（開発中のみ）
                    if args.debug:
                        ui.show_error(str(e))
            
            # フレームレート制御
            clock.tick(2)  # 2FPS（負荷軽減のため低フレームレート）
        
        # 終了処理
        pygame.quit()
        logger.info("アプリケーション正常終了")
        
    except Exception as e:
        logger.critical(f"致命的なエラーが発生: {e}")
        logger.critical(traceback.format_exc())
        # 終了処理
        if ui:
            ui.quit()
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
