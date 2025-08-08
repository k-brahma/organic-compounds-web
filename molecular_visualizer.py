"""
分子の3D可視化機能モジュール
"""

import py3Dmol
import streamlit as st
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MolecularVisualizer:
    """分子の3D可視化を行うクラス"""
    
    def __init__(self):
        self.viewer = None
        self.current_style = 'stick'
        
    def create_3d_viewer(self, mol_block: str, width: int = 800, height: int = 600) -> py3Dmol.view:
        """
        3D分子ビューアーを作成
        
        Args:
            mol_block: MOLブロック形式の分子データ
            width: ビューアーの幅
            height: ビューアーの高さ
            
        Returns:
            py3Dmol.view: 3Dビューアーオブジェクト
        """
        try:
            # py3Dmolビューアーを作成
            self.viewer = py3Dmol.view(width=width, height=height)
            
            # 分子モデルを追加
            self.viewer.addModel(mol_block, 'mol')
            
            # デフォルトスタイルを設定
            self.set_style(self.current_style)
            
            # ビューを中央に配置してズーム調整
            self.viewer.zoomTo()
            
            logger.info("3D viewer created successfully")
            return self.viewer
            
        except Exception as e:
            logger.error(f"Error creating 3D viewer: {e}")
            return None
    
    def set_style(self, style: str, color_scheme: str = 'default') -> None:
        """
        分子の表示スタイルを設定
        
        Args:
            style: 表示スタイル ('stick', 'sphere', 'cartoon', 'line', 'surface')
            color_scheme: 色彩設定
        """
        if self.viewer is None:
            return
            
        try:
            # 現在の表示をクリア
            self.viewer.removeAllModels()
            
            # スタイル設定
            if style == 'stick':
                self.viewer.setStyle({'stick': {'radius': 0.15}})
            elif style == 'sphere':
                self.viewer.setStyle({'sphere': {'radius': 0.5}})
            elif style == 'ball_and_stick':
                self.viewer.setStyle({'stick': {'radius': 0.1}, 'sphere': {'radius': 0.3}})
            elif style == 'line':
                self.viewer.setStyle({'line': {'linewidth': 3}})
            elif style == 'surface':
                self.viewer.addSurface(py3Dmol.VDW, {'opacity': 0.7, 'color': 'blue'})
            elif style == 'cartoon':
                self.viewer.setStyle({'cartoon': {}})
            
            # 色彩設定
            if color_scheme == 'cpk':
                # CPK色彩（元素別標準色）
                pass  # デフォルトでCPK色彩
            elif color_scheme == 'element':
                # 元素別色分け
                self.viewer.setStyle({'stick': {'colorscheme': 'element'}})
            
            self.current_style = style
            
        except Exception as e:
            logger.error(f"Error setting molecular style: {e}")
    
    def add_labels(self, show_atoms: bool = True, show_bonds: bool = False) -> None:
        """
        原子や結合にラベルを追加
        
        Args:
            show_atoms: 原子ラベルを表示するか
            show_bonds: 結合ラベルを表示するか
        """
        if self.viewer is None:
            return
            
        try:
            if show_atoms:
                # 原子にラベルを追加
                self.viewer.addPropertyLabels('elem', 'atom', 
                                            {'fontSize': 12, 'fontColor': 'black'})
        except Exception as e:
            logger.error(f"Error adding labels: {e}")
    
    def set_background_color(self, color: str = 'white') -> None:
        """
        背景色を設定
        
        Args:
            color: 背景色
        """
        if self.viewer is None:
            return
            
        try:
            self.viewer.setBackgroundColor(color)
        except Exception as e:
            logger.error(f"Error setting background color: {e}")
    
    def get_viewer(self) -> Optional[py3Dmol.view]:
        """現在のビューアーオブジェクトを取得"""
        return self.viewer
    
    def render_in_streamlit(self, key: str = "molecule_viewer") -> None:
        """
        StreamlitでHTMLとして表示
        
        Args:
            key: Streamlitコンポーネントのキー
        """
        if self.viewer is None:
            st.error("No molecular viewer available")
            return
            
        try:
            # HTMLを生成して表示
            html = self.viewer._make_html()
            st.components.v1.html(html, width=800, height=600)
            
        except Exception as e:
            logger.error(f"Error rendering in Streamlit: {e}")
            st.error(f"Error rendering molecular viewer: {e}")


def create_interactive_viewer(mol_block: str, 
                            style: str = 'stick',
                            width: int = 800, 
                            height: int = 600,
                            background_color: str = 'white') -> MolecularVisualizer:
    """
    インタラクティブな3D分子ビューアーを作成
    
    Args:
        mol_block: MOLブロック形式の分子データ
        style: 表示スタイル
        width: ビューアーの幅
        height: ビューアーの高さ
        background_color: 背景色
        
    Returns:
        MolecularVisualizer: 設定済みのビジュアライザー
    """
    visualizer = MolecularVisualizer()
    viewer = visualizer.create_3d_viewer(mol_block, width, height)
    
    if viewer:
        visualizer.set_style(style)
        visualizer.set_background_color(background_color)
        
    return visualizer


# 利用可能な表示スタイル
AVAILABLE_STYLES = {
    'stick': 'スティック',
    'sphere': 'スフィア',
    'ball_and_stick': 'ボール&スティック',
    'line': 'ライン',
    'surface': 'サーフェス',
    'cartoon': 'カートゥーン'
}

# 利用可能な色彩設定
AVAILABLE_COLOR_SCHEMES = {
    'default': 'デフォルト',
    'cpk': 'CPK',
    'element': '元素別'
}

# 背景色オプション
BACKGROUND_COLORS = {
    'white': '白',
    'black': '黒',
    'gray': 'グレー',
    'lightblue': 'ライトブルー'
}


if __name__ == "__main__":
    # テスト用のコード
    test_mol_block = """
  Mrv2014 01012023

  3  2  0  0  0  0            999 V2000
   -0.4125    0.7145    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.4125   -0.7145    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  3  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
"""
    
    visualizer = create_interactive_viewer(test_mol_block)
    print("Molecular visualizer created successfully")