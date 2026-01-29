from abc import ABC, abstractmethod
from typing import List, Tuple


class VectorStore(ABC):
    @abstractmethod
    def add(self, vectors: List[List[float]], metadatas: List[dict]):
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 5) -> List[dict]:
        pass
