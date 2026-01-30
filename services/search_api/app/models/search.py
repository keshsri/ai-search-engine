from pydantic import BaseModel
from typing import List

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    document_id: str
    chunk_id: str
    index: int
    content: str