import faiss
import numpy as np
import os
import json
from typing import List, Dict

class FAISSVectorStore:
    def __init__(self, dim: int, index_path: str = "faiss.index", metadata_path: str = "faiss_meta.json"):
        self.dim = dim
        self.index_path = index_path
        self.metadata_path = metadata_path

        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()

    def _load_or_create_index(self):
        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        return faiss.IndexFlatIP(self.dim)

    def _load_metadata(self) -> List[Dict]:
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return []

    def add(self, vectors: np.ndarray, metadatas: List[Dict]):
        if len(vectors) == 0:
            return

        assert vectors.shape[1] == self.dim

        self.index.add(vectors)
        self.metadata.extend(metadatas)

        self._persist()

    def search(self, query_vector: np.ndarray, top_k: int = 5):
        if self.index.ntotal == 0:
            return []

        scores, indices = self.index.search(query_vector, top_k)

        results = []
        for idx in indices[0]:
            if idx == -1:
                continue
            results.append(self.metadata[idx])

        return results

    def _persist(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
