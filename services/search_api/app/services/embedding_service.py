from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])

        embeddings = self.model.encode(
            texts,
            convert_to_numpy = True,
            normalize_embeddings = True
        )

        return embeddings