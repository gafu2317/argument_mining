import textwrap
from src.models import ArgumentGraph

class MermaidGenerator:
    @staticmethod
    def generate(graph: ArgumentGraph, direction: str = "TD") -> str:
        """
        ArgumentGraphデータをMermaid記法の文字列に変換する。
        """
        lines = [f"graph {direction}"]
        
        # 1. ノードの定義
        for node in graph.nodes:
            # エラー回避: ダブルクォート等を置換
            safe_content = node.content.replace('"', "'").replace("(", "（").replace(")", "）")
            
            # ★変更点: 15文字ごとに <br/> で改行を入れる
            wrapped_content_list = textwrap.wrap(safe_content, width=15)
            wrapped_content = "<br/>".join(wrapped_content_list)
            
            # 表示テキスト作成
            display_text = f"{wrapped_content}"
            if node.speaker:
                display_text += f"<br/><small>by {node.speaker}</small>"
            
            # ノードタイプに応じた形状と色の定義
            if node.type == "issue":
                # 丸形 ((Text)) - 黄色系
                lines.append(f'    {node.id}(("{display_text}"))')
                lines.append(f'    style {node.id} fill:#fff3cd,stroke:#d6b656,stroke-width:4px,color:#333')
                
            elif node.type == "decision":
                # 六角形 {{Text}} - 緑系
                lines.append(f'    {node.id}{{{{"{display_text}"}}}}')
                lines.append(f'    style {node.id} fill:#d4edda,stroke:#155724,stroke-width:4px,color:#155724')
                
            elif node.type == "argument":
                # タグ型 >Text] - グレー系
                lines.append(f'    {node.id}>"{display_text}"]')
                lines.append(f'    style {node.id} fill:#f8f9fa,stroke:#6c757d,stroke-width:2px,stroke-dasharray: 5 5,color:#555')
                
            else: # position
                # 四角 [Text] - 青系
                lines.append(f'    {node.id}["{display_text}"]')
                lines.append(f'    style {node.id} fill:#cce5ff,stroke:#b8daff,stroke-width:2px,color:#004085')

        # 2. エッジ（線）の定義
        for edge in graph.edges:
            if edge.label:
                lines.append(f"    {edge.source} -- {edge.label} --> {edge.target}")
            else:
                lines.append(f"    {edge.source} --> {edge.target}")

        return "\n".join(lines)