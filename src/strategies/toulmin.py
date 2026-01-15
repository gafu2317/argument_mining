from src.strategies.base import MiningStrategy
from src.models import ArgumentGraph

class ToulminStrategy(MiningStrategy):
    def analyze(self, text: str) -> ArgumentGraph:
        # 将来的な拡張用
        return ArgumentGraph(nodes=[], edges=[])
