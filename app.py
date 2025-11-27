"""
有機化合物立体構造シミュレーター - Streamlit Webアプリケーション
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from molecular_simulator import MolecularSimulator, get_preset_molecules
from molecular_visualizer import MolecularVisualizer, AVAILABLE_STYLES, BACKGROUND_COLORS
import py3Dmol
from typing import Optional
import logging

# ページ設定
st.set_page_config(
    page_title="有機化合物立体構造シミュレーター",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スタイル設定
st.markdown("""
<style>
    /* メインコンテナのパディングを削減 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .molecule-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    /* 3Dmol iframeコンテナを全幅に */
    .stElementContainer:has(iframe[title="st.iframe"]) {
        width: 100% !important;
    }
    .stIFrame {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# ログ設定
logging.basicConfig(level=logging.INFO)

def initialize_session_state():
    """セッション状態の初期化"""
    if 'simulator' not in st.session_state:
        st.session_state.simulator = MolecularSimulator()
    if 'current_molecule' not in st.session_state:
        st.session_state.current_molecule = None
    if 'molecule_generated' not in st.session_state:
        st.session_state.molecule_generated = False
    if 'properties_calculated' not in st.session_state:
        st.session_state.properties_calculated = False

def render_molecule_3d(mol_block: str, style: str = 'stick'):
    """3D分子構造をレンダリング"""
    try:
        # スタイル設定を準備
        if style == 'stick':
            style_spec = "{'stick': {'radius': 0.2}}"
        elif style == 'sphere':
            style_spec = "{'sphere': {'radius': 0.5}}"
        elif style == 'ball_and_stick':
            style_spec = "{'stick': {'radius': 0.15}, 'sphere': {'radius': 0.3}}"
        elif style == 'line':
            style_spec = "{'line': {'linewidth': 3}}"
        else:
            style_spec = "{'stick': {'radius': 0.2}}"

        # mol_blockをJavaScript用にエスケープ
        mol_block_escaped = mol_block.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

        # 動的にサイズを取得してレンダリングするHTML
        responsive_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://3dmol.org/build/3Dmol-min.js"></script>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                html, body {{ width: 100%; height: 100%; overflow: hidden; }}
                #mol-viewer {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div id="mol-viewer"></div>
            <script>
                const molData = `{mol_block_escaped}`;
                const container = document.getElementById('mol-viewer');
                const viewer = $3Dmol.createViewer(container, {{
                    backgroundColor: 'white'
                }});
                viewer.addModel(molData, 'mol');
                viewer.setStyle({style_spec});
                viewer.zoomTo();
                viewer.render();

                // ウィンドウリサイズ時に再レンダリング
                window.addEventListener('resize', function() {{
                    viewer.resize();
                    viewer.render();
                }});
            </script>
        </body>
        </html>
        """
        st.components.v1.html(responsive_html, width=None, height=650, scrolling=False)

    except Exception as e:
        st.error(f"3D表示エラー: {e}")

def main():
    """メインアプリケーション"""
    initialize_session_state()
    
    # ヘッダー
    st.markdown('<h1 class="main-header">🧪 有機化合物立体構造シミュレーター</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    この アプリケーションでは、SMILES記法を使用して有機化合物の3D立体構造を生成し、
    分子の物理化学的性質を計算・可視化できます。
    """)
    
    # サイドバー設定
    with st.sidebar:
        st.markdown('<h2 class="section-header">⚙️ 設定</h2>', unsafe_allow_html=True)
        
        # 分子入力方法の選択
        input_method = st.radio(
            "分子入力方法",
            ["SMILES記法で入力", "プリセットから選択"],
            index=0
        )
        
        # 分子入力
        if input_method == "SMILES記法で入力":
            smiles = st.text_input(
                "SMILES記法を入力",
                value="CCO",
                help="例: CCO (エタノール), c1ccccc1 (ベンゼン)"
            )
        else:
            preset_molecules = get_preset_molecules()
            selected_preset = st.selectbox(
                "プリセット分子を選択",
                list(preset_molecules.keys()),
                index=0
            )
            smiles = preset_molecules[selected_preset]
            st.code(f"SMILES: {smiles}")
        
        # 最適化設定
        st.markdown("### 🔧 最適化設定")
        max_iterations = st.slider(
            "最大反復回数",
            min_value=50,
            max_value=500,
            value=200,
            step=50
        )
        
        # 可視化設定
        st.markdown("### 🎨 可視化設定")
        visualization_style = st.selectbox(
            "表示スタイル",
            options=list(AVAILABLE_STYLES.keys()),
            format_func=lambda x: AVAILABLE_STYLES[x],
            index=0
        )
        
        show_labels = st.checkbox("原子ラベル表示", value=False)
        
        # 分子生成ボタン
        generate_button = st.button(
            "🚀 3D構造生成",
            type="primary",
            use_container_width=True
        )
    
    # メインコンテンツエリア - 3D分子構造（上段）
    st.markdown('<h2 class="section-header">📊 3D分子構造</h2>',
               unsafe_allow_html=True)

    if generate_button or st.session_state.molecule_generated:
        if generate_button:
            # 分子を生成
            with st.spinner("分子構造を生成中..."):
                simulator = st.session_state.simulator

                if simulator.create_molecule_from_smiles(smiles):
                    if simulator.optimize_3d_structure(max_iterations):
                        st.session_state.molecule_generated = True
                        st.session_state.current_molecule = smiles
                        st.success("✅ 3D構造が正常に生成されました！")
                    else:
                        st.error("❌ 3D構造の最適化に失敗しました")
                        return
                else:
                    st.error("❌ 無効なSMILES記法です")
                    return

        # 3D可視化
        if st.session_state.molecule_generated:
            simulator = st.session_state.simulator
            mol_block = simulator.get_mol_block()

            if mol_block:
                try:
                    render_molecule_3d(mol_block, visualization_style)
                except Exception as e:
                    st.error(f"3D表示エラー: {e}")
                    st.info("💡 代替表示: 分子構造データ")
                    with st.expander("MOLブロックデータ"):
                        st.code(mol_block)
            else:
                st.error("分子データが利用できません")
    else:
        st.info("👈 サイドバーから分子を選択して「3D構造生成」ボタンを押してください")

        # デモ用のプレースホルダー
        st.markdown("""
        ### 🔬 使用可能な機能:
        - **SMILES記法から3D構造生成**: 化学構造式から立体構造を自動生成
        - **エネルギー最適化**: 分子力学計算による安定構造の探索
        - **インタラクティブ3D表示**: マウスで回転・ズーム可能な分子モデル
        - **分子特性計算**: 物理化学的性質の詳細分析
        - **プリセット分子**: よく使われる化合物のワンクリック選択
        """)

    # 分子特性（下段）
    st.markdown("---")
    st.markdown('<h2 class="section-header">📈 分子特性</h2>',
               unsafe_allow_html=True)

    if st.session_state.molecule_generated:
        simulator = st.session_state.simulator

        # 分子特性を計算
        if st.button("🧮 特性計算", use_container_width=True):
            with st.spinner("分子特性を計算中..."):
                properties = simulator.calculate_properties()
                st.session_state.properties_calculated = True

        if st.session_state.properties_calculated:
            properties = simulator.properties

            if properties:
                # 基本情報・Lipinski・その他を横並びで表示
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("### 📋 基本情報")
                    st.metric("分子式", properties.get('formula', 'N/A'))
                    st.metric("分子量", f"{properties.get('molecular_weight', 0):.2f} g/mol")
                    st.metric("重原子数", properties.get('heavy_atoms', 'N/A'))

                with col2:
                    st.markdown("### 💊 Drug-likeness")
                    violations = properties.get('lipinski_violations', 0)
                    if violations == 0:
                        st.success(f"✅ Lipinski違反: {violations}個")
                    elif violations <= 1:
                        st.warning(f"⚠️ Lipinski違反: {violations}個")
                    else:
                        st.error(f"❌ Lipinski違反: {violations}個")
                    st.metric("LogP", f"{properties.get('logp', 0):.2f}")
                    st.metric("TPSA", f"{properties.get('tpsa', 0):.2f} Ų")
                    st.metric("HBD / HBA", f"{properties.get('hbd', 'N/A')} / {properties.get('hba', 'N/A')}")

                with col3:
                    st.markdown("### 🔬 その他の特性")
                    st.metric("回転可能結合数", properties.get('rotatable_bonds', 'N/A'))
                    st.metric("環の数", properties.get('rings', 'N/A'))
                    st.metric("芳香環の数", properties.get('aromatic_rings', 'N/A'))

                # 詳細データとレーダーチャートを横並び
                col_left, col_right = st.columns(2)

                with col_left:
                    with st.expander("📊 詳細データテーブル", expanded=False):
                        df = simulator.get_properties_dataframe()
                        st.dataframe(df, use_container_width=True)

                with col_right:
                    with st.expander("📊 特性可視化", expanded=True):
                        # レーダーチャート用のデータ準備
                        radar_data = {
                            'Property': ['MW', 'LogP', 'TPSA', 'HBD', 'HBA', 'RotBonds'],
                            'Value': [
                                min(properties.get('molecular_weight', 0) / 500, 1),
                                min(properties.get('logp', 0) / 5, 1),
                                min(properties.get('tpsa', 0) / 140, 1),
                                min(properties.get('hbd', 0) / 5, 1),
                                min(properties.get('hba', 0) / 10, 1),
                                min(properties.get('rotatable_bonds', 0) / 10, 1)
                            ]
                        }

                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=radar_data['Value'],
                            theta=radar_data['Property'],
                            fill='toself',
                            name='分子特性'
                        ))

                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 1]
                                )),
                            showlegend=False,
                            height=300,
                            margin=dict(l=40, r=40, t=20, b=20)
                        )

                        st.plotly_chart(fig, use_container_width=True)

            else:
                st.error("特性計算に失敗しました")
    else:
        st.info("まず分子を生成してください")
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🧪 有機化合物立体構造シミュレーター | Powered by RDKit & Streamlit</p>
        <p>分子化学の学習と研究をサポートします</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()