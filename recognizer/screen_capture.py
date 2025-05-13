#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
画面キャプチャモジュール

このモジュールは、画面の特定領域をキャプチャし、画像として取得する機能を提供します。
雀魂（じゃんたま/Mahjong Soul）の画面から手牌や副露などの情報を抽出するために使用します。
"""

import os
import sys
import time
import numpy as np
import cv2
from PIL import ImageGrab, Image
import win32gui
import win32con
import argparse
from pathlib import Path


class ScreenCapture:
    """画面キャプチャクラス"""
    
    def __init__(self, regions=None):
        """
        初期化
        
        Parameters
        ----------
        regions : dict, optional
            キャプチャする領域の辞書（デフォルト: None）
            例: {'hand': (x1, y1, x2, y2), 'dora': (x1, y1, x2, y2)}
        """
        # デフォルトの領域設定
        self.default_regions = {
            'hand': (210, 650, 1070, 720),     # 手牌エリア
            'dora': (800, 300, 950, 350),      # ドラ表示エリア
            'river': (300, 450, 700, 580),     # 自分の河
            'melds': (1090, 650, 1320, 720),   # 副露エリア
            'whole_screen': (0, 0, 1920, 1080) # 全画面（解像度に合わせて調整）
        }
        
        # 領域設定
        self.regions = regions if regions else self.default_regions
        
        # 最後にキャプチャした画像を保存
        self.last_captures = {}
        
        # キャプチャ間隔
        self.min_capture_interval = 0.1  # 秒
        self.last_capture_time = 0
    
    def set_region(self, region_name, coordinates):
        """
        特定の領域の座標を設定する
        
        Parameters
        ----------
        region_name : str
            領域の名前
        coordinates : tuple
            領域の座標 (x1, y1, x2, y2)
        """
        self.regions[region_name] = coordinates
    
    def capture_region(self, region_name):
        """
        指定された領域をキャプチャする
        
        Parameters
        ----------
        region_name : str
            キャプチャする領域の名前
            
        Returns
        -------
        ndarray
            キャプチャした画像（OpenCV形式: BGR）
        """
        # 領域の存在確認
        if region_name not in self.regions:
            return None  # 領域が存在しない場合はNoneを返す
        
        # キャプチャ間隔の制限
        current_time = time.time()
        if current_time - self.last_capture_time < self.min_capture_interval:
            time.sleep(self.min_capture_interval - (current_time - self.last_capture_time))
        
        # 領域の取得
        x1, y1, x2, y2 = self.regions[region_name]
        
        # スクリーンキャプチャ
        try:
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.last_capture_time = time.time()
            
            # PIL形式からOpenCV形式（BGR）に変換
            image = np.array(screenshot)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # キャプチャした画像を保存
            self.last_captures[region_name] = image
            
            return image
        except Exception as e:
            print(f"画面キャプチャ中にエラーが発生しました: {e}")
            # エラーの場合は黒画像を返す
            return np.zeros((y2-y1, x2-x1, 3), dtype=np.uint8)
    
    def capture_all_regions(self):
        """
        すべての定義された領域をキャプチャする
        
        Returns
        -------
        dict
            領域名をキー、キャプチャした画像を値とする辞書
        """
        captures = {}
        for region_name in self.regions.keys():
            captures[region_name] = self.capture_region(region_name)
        
        return captures
    
    def capture_game_screen(self):
        """
        ゲーム画面全体をキャプチャし、必要な領域を抽出する
        
        Returns
        -------
        dict
            ゲーム状態の情報を含む辞書
        """
        # 全画面キャプチャ
        screen = self.capture_region('whole_screen')
        
        # 各領域の抽出
        hand_img = self.capture_region('hand')
        dora_img = self.capture_region('dora')
        river_img = self.capture_region('river')
        melds_img = self.capture_region('melds')
        
        # 相手の河と副露（設定されていれば）
        right_river_img = self.capture_region('right_river')
        oppo_river_img = self.capture_region('opposite_river')
        left_river_img = self.capture_region('left_river')
        
        right_melds_img = self.capture_region('right_melds')
        oppo_melds_img = self.capture_region('opposite_melds')
        left_melds_img = self.capture_region('left_melds')
        
        return {
            'screen': screen,
            'hand': hand_img,
            'dora': dora_img,
            'river': river_img,
            'melds': melds_img,
            'right_river': right_river_img,
            'opposite_river': oppo_river_img,
            'left_river': left_river_img,
            'right_melds': right_melds_img,
            'opposite_melds': oppo_melds_img,
            'left_melds': left_melds_img
        }
    
    def find_window_by_title(self, title_keyword):
        """
        タイトルに特定のキーワードが含まれるウィンドウを検索し、そのウィンドウの座標を取得する
        
        Parameters
        ----------
        title_keyword : str
            ウィンドウタイトルに含まれるキーワード
            
        Returns
        -------
        tuple
            ウィンドウの座標 (x, y, width, height) または None
        """
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title_keyword.lower() in window_title.lower():
                    rect = win32gui.GetWindowRect(hwnd)
                    x = rect[0]
                    y = rect[1]
                    width = rect[2] - x
                    height = rect[3] - y
                    windows.append((hwnd, x, y, width, height))
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        if windows:
            # 最初に見つかったウィンドウを使用
            hwnd, x, y, width, height = windows[0]
            return (x, y, width, height)
        else:
            return None
    
    def save_last_capture(self, region_name, output_dir):
        """
        最後にキャプチャした画像を保存する
        
        Parameters
        ----------
        region_name : str
            保存する領域の名前
        output_dir : str
            保存先ディレクトリ
        """
        if region_name not in self.last_captures:
            print(f"領域 '{region_name}' のキャプチャがありません")
            return
        
        # 出力ディレクトリの作成
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # ファイル名の生成
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{region_name}_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        
        # 画像の保存
        cv2.imwrite(filepath, self.last_captures[region_name])
        print(f"画像を保存しました: {filepath}")
    
    def setup_regions_interactive(self):
        """
        対話モードで各領域の座標を設定する
        """
        print("画面領域設定ウィザードを開始します")
        print("この機能を使用すると、画面の各部分を選択して座標を設定できます")
        
        try:
            # 全画面キャプチャ
            screen = np.array(ImageGrab.grab())
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            # ウィンドウの作成
            cv2.namedWindow("Screen Setup", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Screen Setup", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            # 領域設定
            regions_to_set = [
                ('hand', '手牌エリア'),
                ('dora', 'ドラ表示エリア'),
                ('river', '自分の河'),
                ('melds', '副露エリア'),
                ('right_river', '右家の河'),
                ('opposite_river', '対面の河'),
                ('left_river', '左家の河'),
                ('right_melds', '右家の副露'),
                ('opposite_melds', '対面の副露'),
                ('left_melds', '左家の副露')
            ]
            
            for region_name, region_desc in regions_to_set:
                print(f"\n{region_desc}を選択してください:")
                print("画面上でマウスをドラッグして領域を選択し、ENTERキーを押して確定します")
                print("この領域をスキップする場合は、何も選択せずにENTERキーを押してください")
                
                # 領域選択用の矩形
                roi = cv2.selectROI("Screen Setup", screen, False, False)
                
                if roi[2] > 0 and roi[3] > 0:  # 幅と高さが正の値
                    x, y, w, h = roi
                    self.regions[region_name] = (x, y, x+w, y+h)
                    print(f"{region_desc}の座標: {self.regions[region_name]}")
                else:
                    print(f"{region_desc}の選択をスキップしました")
            
            cv2.destroyAllWindows()
            print("\n領域設定が完了しました")
            
            # 設定を保存
            self.save_regions_config()
            
        except Exception as e:
            cv2.destroyAllWindows()
            print(f"領域設定中にエラーが発生しました: {e}")
    
    def setup_regions_interactive_with_list(self, regions_list):
        """
        指定された領域リストを用いて対話モードで各領域の座標を設定する
        
        Parameters
        ----------
        regions_list : list
            設定する領域のリスト [(region_name, region_description), ...]
        """
        print("画面領域設定ウィザードを開始します")
        print("この機能を使用すると、画面の各部分を選択して座標を設定できます")
        
        try:
            # 全画面キャプチャ
            screen = np.array(ImageGrab.grab())
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            # ウィンドウの作成
            cv2.namedWindow("Screen Setup", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Screen Setup", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            for region_name, region_desc in regions_list:
                print(f"\n{region_desc}を選択してください:")
                print("画面上でマウスをドラッグして領域を選択し、ENTERキーを押して確定します")
                print("この領域をスキップする場合は、何も選択せずにENTERキーを押してください")
                
                # 領域選択用の矩形
                roi = cv2.selectROI("Screen Setup", screen, False, False)
                
                if roi[2] > 0 and roi[3] > 0:  # 幅と高さが正の値
                    x, y, w, h = roi
                    self.regions[region_name] = (x, y, x+w, y+h)
                    print(f"{region_desc}の座標: {self.regions[region_name]}")
                else:
                    print(f"{region_desc}の選択をスキップしました")
            
            cv2.destroyAllWindows()
            print("\n領域設定が完了しました")
            
            # 設定を保存
            self.save_regions_config()
            
        except Exception as e:
            cv2.destroyAllWindows()
            print(f"領域設定中にエラーが発生しました: {e}")
    
    def save_regions_config(self, config_file="screen_regions.cfg"):
        """
        領域設定を設定ファイルに保存する
        
        Parameters
        ----------
        config_file : str
            設定ファイルのパス
        """
        try:
            with open(config_file, 'w') as f:
                for region_name, coords in self.regions.items():
                    f.write(f"{region_name}:{coords[0]},{coords[1]},{coords[2]},{coords[3]}\n")
            print(f"領域設定を保存しました: {config_file}")
        except Exception as e:
            print(f"設定の保存中にエラーが発生しました: {e}")
    
    def load_regions_config(self, config_file="screen_regions.cfg"):
        """
        領域設定を設定ファイルから読み込む
        
        Parameters
        ----------
        config_file : str
            設定ファイルのパス
            
        Returns
        -------
        bool
            読み込みに成功したかどうか
        """
        try:
            if not os.path.exists(config_file):
                print(f"設定ファイル '{config_file}' が見つかりません")
                return False
            
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) != 2:
                        continue
                    
                    region_name = parts[0].strip()
                    coords_str = parts[1].strip()
                    coords = tuple(map(int, coords_str.split(',')))
                    
                    if len(coords) == 4:
                        self.regions[region_name] = coords
            
            print(f"領域設定を読み込みました: {config_file}")
            return True
        except Exception as e:
            print(f"設定の読み込み中にエラーが発生しました: {e}")
            return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='画面キャプチャツール')
    parser.add_argument('--setup', action='store_true', help='画面領域設定ウィザードを起動')
    parser.add_argument('--capture', action='store_true', help='画面をキャプチャして保存')
    parser.add_argument('--output', type=str, default='captures', help='キャプチャ画像の保存先ディレクトリ')
    
    args = parser.parse_args()
    
    # 画面キャプチャクラスの初期化
    screen_capture = ScreenCapture()
    
    # 設定ファイルの読み込み
    config_file = "screen_regions.cfg"
    if os.path.exists(config_file):
        screen_capture.load_regions_config(config_file)
    
    # 画面領域設定ウィザード
    if args.setup:
        screen_capture.setup_regions_interactive()
        return
    
    # 画面キャプチャと保存
    if args.capture:
        captures = screen_capture.capture_all_regions()
        for region_name, image in captures.items():
            if image is not None:
                screen_capture.save_last_capture(region_name, args.output)
        return
    
    # デモ表示モード
    print("デモ表示モードを開始します（終了するには 'q' キーを押してください）")
    try:
        while True:
            captures = screen_capture.capture_all_regions()
            
            # 各領域の表示
            for region_name, image in captures.items():
                if image is not None and image.size > 0:  # 画像が有効な場合
                    cv2.imshow(f"Region: {region_name}", image)
            
            # キー入力の確認
            key = cv2.waitKey(100) & 0xFF
            if key == ord('q'):
                break
            
            time.sleep(0.1)
    
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
