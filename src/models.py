from typing import List, Optional
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    content: str # UI表示用の要約
    original_text: str | None = None # ベクトル化に使用する、会話ログからの生の抜粋
    speaker: str | None = None
    type: str
    sequence: int | None = None
    embedding: list[float] | None = None
    cosine_sim_to_first: float | None = None
    euclidean_distance_to_first: float | None = None
    similarity_to_previous: float | None = None
    distance_from_previous: float | None = None


class Edge(BaseModel):
    source: str
    target: str
    label: str

class ArgumentGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
