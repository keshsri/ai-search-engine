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
    document_title: str = "Unknown"  # Optional with default
    score: float = 0.0  # Optional with default