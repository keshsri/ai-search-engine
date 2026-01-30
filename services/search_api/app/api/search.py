from fastapi import APIRouter, Depends
from app.models.search import SearchRequest, SearchResult
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService
from app.dependencies import get_vector_store
from typing import List

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=List[SearchResult])
def semantic_search(
    request: SearchRequest,
    vector_store=Depends(get_vector_store)
):
    embedding_service = EmbeddingService()
    search_service = SearchService(embedding_service, vector_store)
    return search_service.search(request.query, request.top_k)
