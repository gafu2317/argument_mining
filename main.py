import os
import streamlit as st
import numpy as np
from dotenv import load_dotenv

from src.strategies.ibis import IBISStrategy
from src.strategies.toulmin import ToulminStrategy
from src.llm import LLMClient
from src.plotter import TopicMapPlotter
from src.models import ArgumentGraph

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
    # 0. セッションステート初期化
    # ==========================================
    if "graph_data" not in st.session_state:
        st.session_state["graph_data"] = None
    if "color_metric" not in st.session_state:
        st.session_state["color_metric"] = "ユークリッド距離"
    if "color_comparison" not in st.session_state:
        st.session_state["color_comparison"] = "開始点からの距離"


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
        use_color_analysis = st.checkbox("色分け分析を実行する", value=True)
        
        if use_color_analysis:
            st.session_state["color_comparison"] = st.radio(
                "色分けの比較対象",
                ["開始点からの距離", "直前のノードとの差分"],
                index=["開始点からの距離", "直前のノードとの差分"].index(st.session_state["color_comparison"])
            )
            st.session_state["color_metric"] = st.radio(
                "色分けの計算指標",
                ["ユークリッド距離", "コサイン類似度"],
                index=["ユークリッド距離", "コサイン類似度"].index(st.session_state["color_metric"])
            )
        
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
                    with st.spinner('AIが議論構造を分析中...'):
                        if "IBIS" in strategy_option:
                            strategy = IBISStrategy()
                        else:
                            strategy = ToulminStrategy()
                        
                        graph = strategy.analyze(text_area_val)
                        # 既存の計算結果をリセット
                        for node in graph.nodes:
                            node.embedding = None
                            node.cosine_sim_to_first = None
                            node.euclidean_distance_to_first = None
                            node.similarity_to_previous = None
                            node.distance_from_previous = None
                        st.session_state["graph_data"] = graph

                    # --- 色分け分析処理 ---
                    if use_color_analysis and graph and graph.nodes:
                        with st.spinner('ベクトル化と距離計算を実行中...'):
                            llm = LLMClient()
                            # ベクトル化には生のテキスト(original_text)を使用
                            node_contents = [node.original_text or "" for node in graph.nodes]
                            vectors = llm.fetch_embeddings(node_contents)
                            
                            for i, node in enumerate(graph.nodes):
                                node.embedding = vectors[i]

                            # --- 距離・類似度計算 ---
                            if len(graph.nodes) > 0:
                                # 最初のノードの距離は0または1に設定
                                graph.nodes[0].distance_from_previous = 0.0
                                graph.nodes[0].similarity_to_previous = 1.0
                                
                                first_node_embedding = np.array(graph.nodes[0].embedding)
                                graph.nodes[0].euclidean_distance_to_first = 0.0
                                graph.nodes[0].cosine_sim_to_first = 1.0


                            for i in range(1, len(graph.nodes)):
                                node_embedding = np.array(graph.nodes[i].embedding)

                                # 1. 直前のノードとの比較
                                prev_node_embedding = np.array(graph.nodes[i-1].embedding)
                                graph.nodes[i].distance_from_previous = np.linalg.norm(node_embedding - prev_node_embedding)
                                if np.linalg.norm(node_embedding) > 0 and np.linalg.norm(prev_node_embedding) > 0:
                                    sim_prev = np.dot(node_embedding, prev_node_embedding) / (np.linalg.norm(node_embedding) * np.linalg.norm(prev_node_embedding))
                                    graph.nodes[i].similarity_to_previous = sim_prev
                                else:
                                    graph.nodes[i].similarity_to_previous = 0.0
                                
                                # 2. 最初のノードとの比較
                                graph.nodes[i].euclidean_distance_to_first = np.linalg.norm(node_embedding - first_node_embedding)
                                if np.linalg.norm(node_embedding) > 0 and np.linalg.norm(first_node_embedding) > 0:
                                    sim_first = np.dot(node_embedding, first_node_embedding) / (np.linalg.norm(node_embedding) * np.linalg.norm(first_node_embedding))
                                    graph.nodes[i].cosine_sim_to_first = sim_first
                                else:
                                    graph.nodes[i].cosine_sim_to_first = 0.0
                            
                            st.session_state["graph_data"] = graph
                            
                except Exception as e:
                    st.error(f"エラー: {e}")

    # ==========================================
    # 2. メインエリア
    # ==========================================
    
    if st.session_state["graph_data"]:
        graph = st.session_state["graph_data"]

        # --- 凡例の動的生成 ---
        legend_color_desc = ""
        if st.session_state["color_comparison"] == "開始点からの距離":
            legend_color_desc = "最初の発言からの話題の距離（近いほど青、遠いほど赤）"
        else: # 直前のノードとの差分
            legend_color_desc = "直前の発言からの話題の変化量（変化が小さいほど青、大きいほど赤）"

        st.markdown(f"""
        <div style="background-color:#f8f9fa; padding:15px; border-radius:8px; border:1px solid #ddd; margin-bottom:20px;">
            <h5 style="margin:0 0 10px 0;">💡 図の見方 (Legend)</h5>
            <p style="margin:0;">会話の進行順にノードが横一直線上に並び、各ノードの色の変化で話題の移り変わりを追います。</p>
            <ul style="font-size: smaller; margin-bottom:0;">
                <li><b>横軸:</b> 会話の進行順（時間）</li>
                <li><b>縦軸:</b> 発言者</li>
                <li><b>ノードの色:</b> {legend_color_desc}</li>
                <li><b>ノードの形:</b> ノードの種類（論点、提案など）</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # --- チャート描画 ---
        # 選択された設定をプロッターに渡す
        timeline_chart = TopicMapPlotter.generate_timeline_plot(
            graph, 
            st.session_state["color_metric"], 
            st.session_state["color_comparison"]
        )
        if timeline_chart:
            st.altair_chart(timeline_chart, use_container_width=True)
        else:
            st.info("分析を実行してください。")

        with st.expander("詳細データを見る"):
            st.json(graph.model_dump())

    else:
        st.info("👈 左のサイドバーから「構造化を実行」してください。")

if __name__ == "__main__":
    main()