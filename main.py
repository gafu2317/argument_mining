import os
import streamlit as st
from dotenv import load_dotenv

from src.strategies.ibis import IBISStrategy
from src.strategies.toulmin import ToulminStrategy
from src.visualizer import MermaidGenerator
from streamlit_mermaid import st_mermaid

load_dotenv()

def load_sample_file(filename):
    path = os.path.join("data", "samples", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def main():
    st.set_page_config(page_title="Argument Miner", layout="wide")
    st.subheader("🧩 議論構造可視化 (Argument Structure)")

    # ==========================================
    # 0. セッションステート初期化 (データの永続化)
    # ==========================================
    # まだデータがない場合、空の箱を用意しておく
    if "graph_data" not in st.session_state:
        st.session_state["graph_data"] = None

    # ==========================================
    # 1. サイドバー (設定と入力)
    # ==========================================
    with st.sidebar:
        st.header("⚙️ 設定")
        
        if os.getenv("OPENAI_API_KEY"):
            st.caption("✅ API Key Active")
        else:
            st.error("API Key missing!")

        strategy_option = st.selectbox("分析モデル", ["IBIS (議論・意思決定)", "Toulmin (論理・正当性)"])
        st.divider()

        input_mode = st.radio("入力ソース", ["📂 サンプル", "📝 直接入力"], horizontal=True)
        
        default_text = ""
        if input_mode == "📂 サンプル":
            sample_dir = os.path.join("data", "samples")
            if not os.path.exists(sample_dir):
                os.makedirs(sample_dir)
            files = [f for f in os.listdir(sample_dir) if f.endswith(".txt")]
            files.sort()
            if files:
                selected_file = st.selectbox("ファイル選択", files)
                default_text = load_sample_file(selected_file)
        
        text_area_val = st.text_area("会話ログ", value=default_text, height=300)
        
        # ボタン処理
        if st.button("🚀 構造化を実行", type="primary", use_container_width=True):
            if not text_area_val.strip():
                st.warning("👈 テキストを入力してください")
            else:
                try:
                    with st.spinner('AIが分析中...'):
                        # 分析実行
                        if "IBIS" in strategy_option:
                            strategy = IBISStrategy()
                        else:
                            strategy = ToulminStrategy()
                        
                        # ★ここが重要: 結果をセッションステートに保存
                        st.session_state["graph_data"] = strategy.analyze(text_area_val)
                        
                except Exception as e:
                    st.error(f"エラー: {e}")

    # ==========================================
    # 2. メインエリア (保存されたデータを常に表示)
    # ==========================================
    
    # データがある場合のみ描画処理を行う
    if st.session_state["graph_data"]:
        graph = st.session_state["graph_data"]
        
        # Mermaid生成 (LR: 横向き)
        mermaid_code = MermaidGenerator.generate(graph, direction="LR")
        
        # 凡例
        st.markdown("""
        <div style="background-color:#f8f9fa; padding:15px; border-radius:8px; border:1px solid #ddd; margin-bottom:20px;">
            <h5 style="margin:0 0 10px 0;">💡 図の見方 (Legend)</h5>
            <span style="margin-right:15px;">🟡 <b>論点</b> ((丸))</span>
            <span style="margin-right:15px;">🔵 <b>提案</b> [四角]</span>
            <span style="margin-right:15px;">⚪ <b>根拠</b> >タグ]</span>
            <span style="margin-right:15px;">🟢 <b>決定</b> {{六角}}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # ボーダー付きコンテナで描画
        with st.container(border=True):
            st.caption("📊 議論構造図")
            st_mermaid(mermaid_code, height=2000)
        
        with st.expander("詳細データを見る"):
            st.json(graph.model_dump())

    else:
        # データがない時の案内
        st.info("👈 左のサイドバーから「構造化を実行」してください。")

if __name__ == "__main__":
    main()