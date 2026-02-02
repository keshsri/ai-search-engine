from app.services.embedding_service import EmbeddingService
from app.vector_store.faiss_vector_store import FAISSVectorStore
from app.models.search import SearchResult
from typing import List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: FAISSVectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        logger.debug("SearchService initialized")

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        logger.info(f"Searching for query: '{query}' (top_k={top_k})")
        
        logger.debug("Generating query embedding")
        query_embedding = self.embedding_service.embed([query])
        
        query_vector = np.array(query_embedding).astype('float32')
        logger.debug(f"Query vector shape: {query_vector.shape}")
        
        logger.debug(f"Searching vector store for top {top_k} results")
        results = self.vector_store.search(query_vector, top_k)
        
        logger.info(f"Found {len(results)} results from vector store")
        
        search_results = [
            SearchResult(
                document_id=r["document_id"],
                chunk_id=r["chunk_id"],
                index=r["index"],
                content=r["content"],
                document_title=r.get("document_title", "Unknown"),
                score=r.get("score", 0.0)
            )
            for r in results
        ]
        
        logger.debug(f"Converted {len(search_results)} results to SearchResult objects")
        
        return search_results

