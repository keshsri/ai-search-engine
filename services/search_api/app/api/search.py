from fastapi import APIRouter, Depends
from app.models.search import SearchRequest, SearchResult
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService
from app.dependencies import get_vector_store
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=List[SearchResult])
def semantic_search(
    request: SearchRequest,
    vector_store=Depends(get_vector_store)
):
    logger.info(f"Search request received: query='{request.query}', top_k={request.top_k}")
    
    embedding_service = EmbeddingService()
    search_service = SearchService(embedding_service, vector_store)
    
    logger.debug("Executing semantic search")
    results = search_service.search(request.query, request.top_k)
    
    logger.info(f"Search completed: found {len(results)} results for query='{request.query}'")
    
    return results
