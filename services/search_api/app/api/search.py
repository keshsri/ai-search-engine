from fastapi import APIRouter, Depends
from app.models.search import SearchRequest, SearchResult
from app.services.search_service import SearchService
from app.services.embedding_service import get_embedding_service
from app.dependencies import get_vector_store
from app.core.exceptions import InvalidSearchQueryException
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=List[SearchResult])
def semantic_search(
    request: SearchRequest,
    vector_store=Depends(get_vector_store)
):
    logger.info(f"Search request received (top_k={request.top_k})")
    
    if not request.query or not request.query.strip():
        logger.warning("Empty search query received")
        raise InvalidSearchQueryException(
            message="Search query cannot be empty",
            details={"query": request.query}
        )
    
    if request.top_k <= 0:
        logger.warning(f"Invalid top_k value: {request.top_k}")
        raise InvalidSearchQueryException(
            message="top_k must be greater than 0",
            details={"top_k": request.top_k}
        )
    
    embedding_service = get_embedding_service()
    search_service = SearchService(embedding_service, vector_store)
    
    logger.debug("Executing semantic search")
    results = search_service.search(request.query, request.top_k)
    
    logger.info(f"Search completed: found {len(results)} results")
    
    return results
