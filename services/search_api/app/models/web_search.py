"""
Data models for web search results.
"""
from pydantic import BaseModel
from typing import Optional


class WebSearchResult(BaseModel):
    """Model for web search result from Tavily."""
    
    title: str
    url: str
    content: str
    score: Optional[float] = None
