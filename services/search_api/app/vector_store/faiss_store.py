import faiss
import numpy as np
from typing import List, Dict

from app.vector_store.base import VectorStore


class FAISSVectorStore(VectorStore):
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: List[Dict] = []

    def add(self, vectors: List[List[float]], metadatas: List[dict]):
        vectors_np = np.array(vectors).astype("float32")
        self.index.add(vectors_np)
        self.metadata.extend(metadatas)

    def search(self, query_vector: List[float], top_k: int = 5) -> List[dict]:
        query_np = np.array([query_vector]).astype("float32")
        distances, indices = self.index.search(query_np, top_k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["score"] = float(distance)
                results.append(result)

        return results
