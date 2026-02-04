from src.strategies.base import MiningStrategy
from src.models import ArgumentGraph
from src.llm import LLMClient

class IBISStrategy(MiningStrategy):
    def analyze(self, text: str) -> ArgumentGraph:
        llm = LLMClient()
        
        # プロンプトを日本語指示向けに調整
        system_prompt = """
あなたは議論構造化のプロフェッショナルです。IBISモデルに基づいて会話ログを構造化してください。

# Definitions (ノードの定義)
- **issue**: 議論の論点や問い (Shape: Circle)
- **position**: 問いに対する提案や意見 (Shape: Rect)
- **argument**: 提案に対する根拠・支持・懸念 (Shape: Tag)
- **decision**: 最終的な決定事項 (Shape: Hexagon)

# Rules (抽出ルール)
1. 会話から主要なIssue(論点)を特定する。
2. それに対するPosition(提案)を特定する。
3. Argument(根拠)を特定し、支持か反対かを明確にする。
4. 結論が出ている場合はDecision(決定)とする。
5. **会話の文脈が大きく変わる場合(話題の分岐)は、無理に既存のノードに関連付けず、新しいIssueとして扱うこと。**
6. **全ての主要な発言を省略せず、それぞれノードとして抽出すること。**
7. **`content`** フィールドには、抽出したノードの内容を **日本語で簡潔に要約** して格納すること。
8. **`original_text`** フィールドには、そのノードの根拠となった会話ログの該当部分を **変更せずにそのまま** 格納すること。
9. 各ノードには、会話ログにおける出現順を示す `sequence` (1から始まる整数) を必ず付与すること。

# Edge Labels (矢印のラベル定義)
以下の日本語ラベルを使用してください：
- Position -> **提案** -> Issue
- Argument -> **支持** -> Position (肯定的な理由)
- Argument -> **懸念** -> Position (否定的な理由・反対意見)
- Decision -> **決定** -> Position (採用された案)
- (関連性の低い Position/Issue 同士は、エッジで結ばない)

# Output Format (JSON)
Strictly output in JSON format matching this schema:
{
  "nodes": [
    {
      "id": "n1",
      "type": "issue",
      "content": "APIの仕様が不明",
      "original_text": "Aさん: それが少し問題で...。APIの仕様について、ドキュメントに記載がない部分があって困っています。",
      "speaker": "Aさん",
      "sequence": 1
    },
    {
      "id": "n2",
      "type": "position",
      "content": "新作ゲームで遊ぶ",
      "original_text": "Cさん: ドキュメントといえば、昨日公開された新しいMMORPGの「クリスタル・ファンタジア」の公式サイト、すごい作り込みだったよね。",
      "speaker": "Cさん",
      "sequence": 2
    }
  ],
  "edges": []
}
Note: `type` must be strictly one of: "issue", "position", "argument", "decision". For edges, use `source` and `target` to link node IDs. Example: `{"source": "n1", "target": "n2", "label": "提案"}`.
"""
        # LLMを実行
        data = llm.fetch_json(system_prompt, text)
        
        # Pydanticモデルに変換
        return ArgumentGraph(**data)