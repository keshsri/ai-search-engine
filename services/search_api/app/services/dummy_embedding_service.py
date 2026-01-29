import hashlib
import random
from typing import List

from app.services.embedding_service import EmbeddingService


class DummyEmbeddingService(EmbeddingService):
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []

        for text in texts:
            # deterministic seed per text
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
            random.seed(seed)

            vector = [random.random() for _ in range(self.dimension)]
            embeddings.append(vector)

        return embeddings
