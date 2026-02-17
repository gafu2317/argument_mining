import pandas as pd
import altair as alt
import textwrap
import colorsys
from .models import ArgumentGraph, Node
from typing import List, Tuple, Optional

_NODE_FONT_SIZE = 9
_NODE_CHARS_PER_LINE = 8
_NODE_MAX_CONTENT_CHARS = _NODE_CHARS_PER_LINE * 2  # 最大2行分
# 話者1行 + 内容最大2行 = 3行のテキストブロックを中央揃えにするためのdy
_NODE_TEXT_DY = -round((_NODE_MAX_CONTENT_CHARS // _NODE_CHARS_PER_LINE) / 2 * _NODE_FONT_SIZE * 1.4)

_NODE_TYPE_LABELS = {
    "issue": "論点", "position": "提案",
    "argument": "根拠", "decision": "決定",
}

class TopicMapPlotter:

    @staticmethod
    def _compute_node_sizes(label_text: str, padding: int = 8) -> Tuple[float, float]:
        """テキスト量に応じたノードボックスの面積（mark_point size）を計算する。
        日本語（全角）は font_size px、ASCII は 0.6 * font_size px として幅を推定。"""
        lines = label_text.split('\n')
        max_line_px = 0.0
        for line in lines:
            line_px = sum(_NODE_FONT_SIZE if ord(c) > 127 else _NODE_FONT_SIZE * 0.6 for c in line)
            max_line_px = max(max_line_px, line_px)
        height_px = len(lines) * _NODE_FONT_SIZE * 1.4
        inner_side = max(max_line_px, height_px) + padding * 2
        outer_side = inner_side + 14  # ボーダー幅 7px
        return outer_side ** 2, inner_side ** 2

    @staticmethod
    def _prepare_node_data(nodes: List[Node], color_metric: str, color_comparison: str) -> Tuple[Optional[pd.DataFrame], str]:
        """ノードデータを準備し、色計算を行う"""
        if not nodes:
            return None, "Default"

        node_data = []
        for node in nodes:
            speaker_prefix = (node.speaker[:6] if node.speaker else "不明")
            content_summary = node.content[:_NODE_MAX_CONTENT_CHARS]
            wrapped_content = '\n'.join(textwrap.wrap(content_summary, width=_NODE_CHARS_PER_LINE))
            type_label = _NODE_TYPE_LABELS.get((node.node_type or "").lower(), "?")
            label_text = f"{speaker_prefix}\n{wrapped_content}"
            # サイズ計算にはtype_labelも含め、ノードが上部ラベルより小さくならないようにする
            outer_size, inner_size = TopicMapPlotter._compute_node_sizes(f"{type_label}\n{label_text}")
            node_data.append({
                "id": node.id, "sequence": node.sequence, "speaker": node.speaker or "不明",
                "node_type": node.node_type or "", "type_label": type_label,
                "content_full": node.content, "label_text": label_text,
                "cosine_sim_to_first": node.cosine_sim_to_first,
                "euclidean_distance_to_first": node.euclidean_distance_to_first,
                "similarity_to_previous": node.similarity_to_previous,
                "distance_from_previous": node.distance_from_previous,
                "value_for_color": 1.0, "tooltip_value": 0.0,
                "outer_size": outer_size, "inner_size": inner_size,
            })
        
        nodes_df = pd.DataFrame(node_data)
        if nodes_df.empty:
            return None, "Default"

        # --- 色計算とツールチップのためのデータ準備 ---
        is_distance = "距離" in color_metric
        is_previous_comparison = "直前" in color_comparison

        if is_previous_comparison:
            value_col = 'distance_from_previous' if is_distance else 'similarity_to_previous'
            tooltip_title = "直前との" + ("距離" if is_distance else "類似度")
        else: # 開始点
            value_col = 'euclidean_distance_to_first' if is_distance else 'cosine_sim_to_first'
            tooltip_title = "開始点との" + ("距離" if is_distance else "類似度")

        if value_col in nodes_df.columns and nodes_df[value_col].notna().any():
            nodes_df['tooltip_value'] = nodes_df[value_col]
            
            if is_distance: # ユークリッド距離
                max_val = nodes_df[value_col].max()
                if max_val > 0:
                    # 距離が大きいほど赤 (色相=0) になるよう反転
                    nodes_df['value_for_color'] = nodes_df[value_col].apply(lambda x: 1 - (x / max_val) if x is not None else 1.0)
                else:
                    nodes_df['value_for_color'] = 1.0 # 全て青
            else: # コサイン類似度
                # 類似度が高いほど青 (色相=0.66)
                # (-1 to 1) -> (0 to 1) for hue
                nodes_df['value_for_color'] = nodes_df[value_col].apply(lambda x: (x + 1) / 2 if x is not None else 0.0)
        
        # --- HSVカラーマッピング処理 ---
        # 0.0 (赤) から 0.66 (青) の範囲で色相を変化させる
        nodes_df['h'] = nodes_df['value_for_color'].apply(lambda x: x * 0.66)
        fixed_s, fixed_v = 0.9, 0.9
        nodes_df['color_rgb'] = nodes_df['h'].apply(
            lambda h: '#%02x%02x%02x' % tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, fixed_s, fixed_v))
        )
            
        return nodes_df, tooltip_title

    @staticmethod
    def generate_timeline_plot(graph: ArgumentGraph, color_metric: str, color_comparison: str):
        """時系列分析チャートを生成する"""
        valid_nodes_df, tooltip_title = TopicMapPlotter._prepare_node_data(graph.nodes, color_metric, color_comparison)
        
        if valid_nodes_df is None or valid_nodes_df.empty:
            return None
        
        # sequenceがNaNの行を除外し、sequence順に並べたうえで表示用インデックスを付与する
        # plot_x を X 軸に使うことで、同一utteranceの複数ノードも等間隔に並ぶ
        valid_nodes_df = valid_nodes_df[valid_nodes_df['sequence'].notna()].sort_values(by='sequence').reset_index(drop=True)
        if valid_nodes_df.empty:
            return None
        valid_nodes_df['plot_x'] = range(len(valid_nodes_df))

        # エッジデータ準備
        edge_data = []
        node_pos_map = {node["id"]: {"plot_x": node["plot_x"], "speaker": node["speaker"]} for _, node in valid_nodes_df.iterrows()}
        for edge in graph.edges:
            source_node_info, target_node_info = node_pos_map.get(edge.source), node_pos_map.get(edge.target)
            if source_node_info and target_node_info:
                edge_data.append({
                    "x1": source_node_info["plot_x"], "y1": source_node_info["speaker"],
                    "x2": target_node_info["plot_x"], "y2": target_node_info["speaker"],
                })
        edges_df = pd.DataFrame(edge_data)

        # グラフ構築
        base = alt.Chart(valid_nodes_df).encode(
            x=alt.X('plot_x:Q', axis=alt.Axis(title='時系列順', grid=True)),
            y=alt.Y('speaker:N', axis=alt.Axis(title='発言者'))
        )
        
        layers = []
        if not edges_df.empty:
            argument_edge_layer = alt.Chart(edges_df).mark_rule(color='gray', opacity=0.6).encode(x='x1:Q', y='y1:N', x2='x2:Q', y2='y2:N')
            layers.append(argument_edge_layer)

        tooltip_content = [
            alt.Tooltip('node_type:N', title='種別'),
            alt.Tooltip('content_full:N', title='内容'),
            alt.Tooltip('id:N', title='ノードID'),
            alt.Tooltip('tooltip_value:Q', title=tooltip_title, format='.3f')
        ]

        border_layer = base.mark_point(shape='square', filled=True, opacity=1.0).encode(
            color=alt.Color('color_rgb:N', scale=None),
            size=alt.Size('outer_size:Q', scale=None, legend=None),
            tooltip=tooltip_content
        )
        white_bg_layer = base.mark_point(shape='square', filled=True, color='white', opacity=1.0).encode(
            size=alt.Size('inner_size:Q', scale=None, legend=None)
        )
        foreground_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=_NODE_FONT_SIZE, color='black',
            lineBreak='\n', dy=_NODE_TEXT_DY
        ).encode(text=alt.Text('label_text:N'))

        type_label_dy = -(int(valid_nodes_df['outer_size'].max() ** 0.5) // 2 + 8)
        type_label_layer = base.mark_text(
            align='center', baseline='bottom', fontSize=_NODE_FONT_SIZE - 1, color='#555555',
            dy=type_label_dy
        ).encode(
            text=alt.Text('type_label:N'),
        )

        layers.extend([border_layer, white_bg_layer, foreground_text_layer, type_label_layer])

        # ノードの最大サイズ（mark_point size は面積なので sqrt で辺長に変換）から
        # バンドの高さを計算する。type_label はノード上端より abs(type_label_dy) 上に描画されるため、
        # バンド高さにその分を加算してクリップされないようにする。
        node_height_px = int(valid_nodes_df['outer_size'].max() ** 0.5)
        label_overhead = abs(type_label_dy) + _NODE_FONT_SIZE * 2
        n_speakers = valid_nodes_df['speaker'].nunique()
        chart_height = n_speakers * (node_height_px + label_overhead + 20)

        chart_width = max(len(valid_nodes_df) * 60 + 80, 350)

        return alt.layer(*layers).properties(
            width=chart_width, height=chart_height
        ).interactive()