import os
import streamlit as st
from dotenv import load_dotenv

from src.strategies.ibis import IBISStrategy
from src.strategies.toulmin import ToulminStrategy
from src.visualizer import MermaidGenerator
from src.llm import LLMClient
from src.clustering import perform_clustering
from src.models import ArgumentGraph
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
        
        # --- クラスタリング設定 ---
        st.divider()
        use_clustering = st.checkbox("トピック別で色分けする (クラスタリング)", value=True)
        num_clusters = 0
        if use_clustering:
            num_clusters = st.number_input("トピック数（色の数）", min_value=2, max_value=10, value=4)
        # --------------------------

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
        
        if st.button("🚀 構造化を実行", type="primary", use_container_width=True):
            if not text_area_val.strip():
                st.warning("👈 テキストを入力してください")
            else:
                try:
                    with st.spinner('AIが分析中...'):
                        if "IBIS" in strategy_option:
                            strategy = IBISStrategy()
                        else:
                            strategy = ToulminStrategy()
                        
                        graph = strategy.analyze(text_area_val)
                        st.session_state["graph_data"] = graph

                    # --- クラスタリング処理 ---
                    if use_clustering and graph and graph.nodes:
                        with st.spinner('ベクトル化とクラスタリングを実行中...'):
                            llm = LLMClient()
                            node_contents = [node.content for node in graph.nodes]
                            
                            vectors = llm.fetch_embeddings(node_contents)
                            cluster_ids = perform_clustering(vectors, num_clusters)
                            
                            for i, node in enumerate(graph.nodes):
                                node.cluster_id = cluster_ids[i]
                            
                            st.session_state["graph_data"] = graph # 更新
                            
                except Exception as e:
                    st.error(f"エラー: {e}")

    # ==========================================
    # 2. メインエリア (保存されたデータを常に表示)
    # ==========================================
    
    if st.session_state["graph_data"]:
        graph = st.session_state["graph_data"]
        
        mermaid_code = MermaidGenerator.generate(graph, direction="LR")
        
        st.markdown("""
        <div style="background-color:#f8f9fa; padding:15px; border-radius:8px; border:1px solid #ddd; margin-bottom:20px;">
            <h5 style="margin:0 0 10px 0;">💡 図の見方 (Legend)</h5>
            <span style="margin-right:15px;">🟡 <b>論点</b> ((丸))</span>
            <span style="margin-right:15px;">🔵 <b>提案</b> [四角]</span>
            <span style="margin-right:15px;">⚪ <b>根拠</b> >タグ]</span>
            <span style="margin-right:15px;">🟢 <b>決定</b> {{六角}}</span>
            <p style="font-size: smaller; margin-top: 10px; margin-bottom: 0;">※ノードの色は話題の近さ(トピック)によって自動で色分けされます。</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            st.caption("📊 議論構造図")
            st_mermaid(mermaid_code, height=2000)
        
        with st.expander("詳細データを見る"):
            st.json(graph.model_dump())

    else:
        st.info("👈 左のサイドバーから「構造化を実行」してください。")

if __name__ == "__main__":
    main()