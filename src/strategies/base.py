from abc import ABC, abstractmethod
from src.models import ArgumentGraph

class MiningStrategy(ABC):
    @abstractmethod
    def analyze(self, text: str) -> ArgumentGraph:
        pass
