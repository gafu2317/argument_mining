import pandas as pd
import altair as alt
import textwrap
import colorsys
from .models import ArgumentGraph

class TopicMapPlotter:
    NODE_TYPE_MAP = {
        'issue': '論点',
        'position': '提案',
        'argument': '根拠',
        'decision': '決定'
    }

    @staticmethod
    def _prepare_node_data(graph: ArgumentGraph, distance_metric: str):
        """共通のノードデータ準備処理"""
        node_data = []
        for node in graph.nodes:
            speaker_prefix = f"{node.speaker}" if node.speaker else "不明"
            content_summary = (node.content[:30] + '...') if len(node.content) > 30 else node.content
            wrapped_content = '\n'.join(textwrap.wrap(content_summary, width=15))
            label_text = f"{speaker_prefix}\n{wrapped_content}"
            
            node_data.append({
                "id": node.id,
                "sequence": node.sequence,
                "speaker": node.speaker or "不明",
                "content_full": node.content,
                "label_text": label_text,
                "type": node.type,
                "type_jp": TopicMapPlotter.NODE_TYPE_MAP.get(node.type, node.type),
                "cosine_sim_to_first": node.cosine_sim_to_first,
                "euclidean_distance_to_first": node.euclidean_distance_to_first,
                "value_for_color": 0.0, # 色計算用の値を初期化
                "tooltip_value": 0.0,
            })
        nodes_df = pd.DataFrame(node_data)
        if nodes_df.empty:
            return None, "Default"

        # --- 色計算とツールチップのためのデータ準備 ---
        tooltip_title = "距離/類似度"
        if distance_metric == "コサイン類似度":
            tooltip_title = "コサイン類似度"
            value_col = 'cosine_sim_to_first'
            if value_col in nodes_df.columns and nodes_df[value_col].notna().any():
                nodes_df['tooltip_value'] = nodes_df[value_col]
                # (-1 to 1) -> (0 to 1) for hue
                nodes_df['value_for_color'] = nodes_df[value_col].apply(lambda x: (x + 1) / 2 if x is not None else 0)

        elif distance_metric == "ユークリッド距離":
            tooltip_title = "ユークリッド距離"
            value_col = 'euclidean_distance_to_first'
            if value_col in nodes_df.columns and nodes_df[value_col].notna().any():
                nodes_df['tooltip_value'] = nodes_df[value_col]
                max_dist = nodes_df[value_col].max()
                if max_dist > 0:
                    # (0 to max_dist) -> (0 to 1) and inverted for hue
                    nodes_df['value_for_color'] = nodes_df[value_col].apply(lambda x: 1 - (x / max_dist) if x is not None else 0)
                else:
                    nodes_df['value_for_color'] = 1.0 # all zero distance

        # --- HSVカラーマッピング処理 ---
        if 'value_for_color' in nodes_df.columns:
            # 0.0 (赤) から 0.66 (青) の範囲で色相を変化させる
            nodes_df['h'] = nodes_df['value_for_color'].apply(lambda x: x * 0.66)
            fixed_s, fixed_v = 0.9, 0.9
            nodes_df['color_rgb'] = nodes_df['h'].apply(
                lambda h: '#%02x%02x%02x' % tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, fixed_s, fixed_v))
            )
        else:
            nodes_df['color_rgb'] = '#808080'
            
        return nodes_df, tooltip_title

    @staticmethod
    def generate_timeline_plot(graph: ArgumentGraph, distance_metric: str):
        """時系列分析チャートを生成する"""
        valid_nodes_df, tooltip_title = TopicMapPlotter._prepare_node_data(graph, distance_metric)
        if valid_nodes_df is None or valid_nodes_df.empty or len(valid_nodes_df) < 2:
            return None
        
        valid_nodes_df = valid_nodes_df[valid_nodes_df['sequence'].notna()].sort_values(by='sequence').reset_index(drop=True)
        if valid_nodes_df.empty:
            return None

        # エッジデータ準備
        edge_data = []
        node_pos_map = {node["id"]: {"sequence": node["sequence"], "speaker": node["speaker"]} for _, node in valid_nodes_df.iterrows()}
        for edge in graph.edges:
            source_node_info, target_node_info = node_pos_map.get(edge.source), node_pos_map.get(edge.target)
            if source_node_info and target_node_info:
                edge_data.append({
                    "x1": source_node_info["sequence"], "y1": source_node_info["speaker"],
                    "x2": target_node_info["sequence"], "y2": target_node_info["speaker"],
                    "label": edge.label,
                    "mid_x": (source_node_info["sequence"] + target_node_info["sequence"]) / 2
                })
        edges_df = pd.DataFrame(edge_data)

        # グラフ構築
        base = alt.Chart(valid_nodes_df).encode(
            x=alt.X('sequence:Q', axis=alt.Axis(title='時系列順', grid=True)),
            y=alt.Y('speaker:N', axis=alt.Axis(title='発言者'))
        )
        argument_edge_layer = alt.Chart(edges_df).mark_rule(color='gray', opacity=0.6).encode(x='x1:Q', y='y1:N', x2='x2:Q', y2='y2:N')
        edge_label_layer = alt.Chart(edges_df).mark_text(
            align='center', baseline='middle', fontSize=9, color='gray', dy=-8
        ).encode(x='mid_x:Q', y='y1:N', text='label:N')

        # 動的なツールチップ
        tooltip_content = [
            alt.Tooltip('content_full:N', title='内容'),
            alt.Tooltip('id:N', title='ノードID'),
            alt.Tooltip('tooltip_value:Q', title=tooltip_title, format='.2f')
        ]

        background_shape_layer = base.mark_point(size=5000, opacity=0.9, filled=True).encode(
            color=alt.Color('color_rgb:N', scale=None),
            shape=alt.Shape('type_jp:N', title="ノード種別", scale=alt.Scale(
                domain=list(TopicMapPlotter.NODE_TYPE_MAP.values()),
                range=['circle', 'square', 'triangle-right', 'diamond']
            )),
            tooltip=tooltip_content
        )
        foreground_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='black', lineBreak='\n', opacity=0.9
        ).encode(text=alt.Text('label_text:N'))

        return (argument_edge_layer + edge_label_layer + background_shape_layer + foreground_text_layer).properties(
            width=700, height=300
        ).interactive()