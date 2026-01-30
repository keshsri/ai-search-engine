from app.services.embedding_service import EmbeddingService
from app.vector_store.faiss_vector_store import FAISSVectorStore
from app.models.search import SearchResult
from typing import List
import numpy as np


class SearchService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: FAISSVectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        # Get query embedding
        query_embedding = self.embedding_service.embed([query])
        
        # Convert to numpy array for FAISS
        query_vector = np.array(query_embedding).astype('float32')
        
        # Search in vector store
        results = self.vector_store.search(query_vector, top_k)

        return [
            SearchResult(
                document_id=r["document_id"],
                chunk_id=r["chunk_id"],
                index=r["index"],
                content=r["content"]
            )
            for r in results
        ]

