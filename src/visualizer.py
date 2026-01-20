import textwrap
from src.models import ArgumentGraph

class MermaidGenerator:
    # クラスターごとの色分け定義 (fill, stroke)
    CLUSTER_COLORS = [
        {"fill": "#E3F2FD", "stroke": "#90CAF9"}, # Light Blue
        {"fill": "#E8F5E9", "stroke": "#A5D6A7"}, # Light Green
        {"fill": "#FFFDE7", "stroke": "#FFF59D"}, # Light Yellow
        {"fill": "#FBE9E7", "stroke": "#FFAB91"}, # Light Deep Orange
        {"fill": "#F3E5F5", "stroke": "#CE93D8"}, # Light Purple
        {"fill": "#EFEBE9", "stroke": "#BCAAA4"}, # Light Brown
        {"fill": "#E0F7FA", "stroke": "#80DEEA"}, # Light Cyan
        {"fill": "#FCE4EC", "stroke": "#F48FB1"}, # Light Pink
    ]

    @staticmethod
    def generate(graph: ArgumentGraph, direction: str = "TD") -> str:
        lines = [f"graph {direction}"]
        
        for node in graph.nodes:
            safe_content = node.content.replace('"', "'").replace("(", "（").replace(")", "）")
            wrapped_content_list = textwrap.wrap(safe_content, width=15)
            wrapped_content = "<br/>".join(wrapped_content_list)
            
            display_text = f"{wrapped_content}"
            if node.speaker:
                display_text += f"<br/><small>by {node.speaker}</small>"
            
            # 1. ノード形状を決定
            shape_and_text = {
                "issue": f'(("{display_text}"))',
                "decision": f'{{{{"{display_text}"}}}}',
                "argument": f'>"{display_text}"]',
                "position": f'["{display_text}"]'
            }.get(node.type, f'["{display_text}"]') # デフォルトは position
            
            lines.append(f'    {node.id}{shape_and_text}')

            # 2. ノードスタイル (色) を決定
            # クラスターIDがあれば、それを優先して色付け
            if node.cluster_id is not None:
                color_scheme = MermaidGenerator.CLUSTER_COLORS[node.cluster_id % len(MermaidGenerator.CLUSTER_COLORS)]
                lines.append(f'    style {node.id} fill:{color_scheme["fill"]},stroke:{color_scheme["stroke"]},stroke-width:3px,color:#333')
            else:
                # クラスターIDがなければ、従来のタイプ別色付け
                if node.type == "issue":
                    lines.append(f'    style {node.id} fill:#fff3cd,stroke:#d6b656,stroke-width:4px,color:#333')
                elif node.type == "decision":
                    lines.append(f'    style {node.id} fill:#d4edda,stroke:#155724,stroke-width:4px,color:#155724')
                elif node.type == "argument":
                    lines.append(f'    style {node.id} fill:#f8f9fa,stroke:#6c757d,stroke-width:2px,stroke-dasharray: 5 5,color:#555')
                else: # position
                    lines.append(f'    style {node.id} fill:#cce5ff,stroke:#b8daff,stroke-width:2px,color:#004085')

        # 3. エッジの定義
        for edge in graph.edges:
            if edge.label:
                lines.append(f"    {edge.source} -- {edge.label} --> {edge.target}")
            else:
                lines.append(f"    {edge.source} --> {edge.target}")

        return "\n".join(lines)