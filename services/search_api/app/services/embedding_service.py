from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import logging

from app.core.exceptions import EmbeddingException

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        logger.info("Initializing EmbeddingService with model: all-MiniLM-L6-v2")
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info(f"Model loaded successfully. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise EmbeddingException(
                message="Failed to initialize embedding model",
                details={"error": str(e)}
            )

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            logger.warning("Empty text list provided for embedding, returning empty array")
            return np.array([])

        logger.debug(f"Generating embeddings for {len(texts)} texts")
        logger.debug(f"Average text length: {sum(len(t) for t in texts) / len(texts):.1f} characters")

        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy = True,
                normalize_embeddings = True
            )
            logger.info(f"Successfully generated {len(embeddings)} embeddings with shape {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: error={str(e)}")
            raise EmbeddingException(
                message="Failed to generate embeddings",
                details={"error": str(e), "text_count": len(texts)}
            )