ユークリッド距離かコサイン類似度を使って次元数を削減せずに色に変換する
HSVも使ってみる
実際のユークリッド距離やコサイン類似度を表示する
仮説として色の変化が話題の脱線とリンクしている
    話題がずれていないのに、色が変わりすぎていることは避けたい



```Python
                    # --- 色分け分析処理 ---
                    if use_color_analysis and graph and graph.nodes:
                        with st.spinner('ベクトル化と距離計算を実行中...'):
                            llm = LLMClient()
                            node_contents = [node.content for node in graph.nodes]
                            vectors = llm.fetch_embeddings(node_contents)
                            
                            for i, node in enumerate(graph.nodes):
                                node.embedding = vectors[i]

                            if graph.nodes and len(graph.nodes) > 1:
                                first_node_embedding = np.array(graph.nodes[0].embedding)
                                for node in graph.nodes:
                                    if node.embedding is not None:
                                        node_embedding = np.array(node.embedding)
                                        # コサイン類似度
                                        if np.linalg.norm(first_node_embedding) > 0 and np.linalg.norm(node_embedding) > 0:
                                            sim = np.dot(node_embedding, first_node_embedding) / (np.linalg.norm(node_embedding) * np.linalg.norm(first_node_embedding))
                                            node.cosine_sim_to_first = sim
                                        else:
                                            node.cosine_sim_to_first = 0.0
                                        
                                        # ユークリッド距離
                                        dist = np.linalg.norm(node_embedding - first_node_embedding)
                                        node.euclidean_distance_to_first = dist
                            
                            st.session_state["graph_data"] = graph

```
極端な逸脱をログをつける
逸脱をした後に元の話題に戻す
ユークリッドでもやってみる
コサイン類似度の実装をみる

ユークリッド距離もコサイン類似度も、直前のノードとどのくらい違うかを比較している
コサイン類似度1が完全一致0が無関係(1（同じ向き）〜0（直交・無関係）〜-1（逆向き）)
ユークリッド距離0が完全一致、数値が大きくなるほど無関係
ただし、コードで0~1に正規化している
0が無関係、１が一致

基準ノードとほぼ同じ内容	1.0 に近い	青（冷たい色）
中間の類似度	0.5 前後	緑〜黄
基準ノードと全く違う内容	0.0 に近い	赤（熱い色）

これから
Louvain法でコミュニティ検出による「グループ分け」
K-meansクラスタリングによる「トピック分類」