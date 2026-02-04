"""
Tavily service for web search integration.
"""
import logging
from typing import List
from tavily import TavilyClient

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException
from app.models.web_search import WebSearchResult

logger = logging.getLogger(__name__)


class TavilyService:
    """Service for web search using Tavily API."""
    
    def __init__(self):
        """Initialize Tavily client."""
        if not settings.TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY not configured. Web search will be unavailable.")
            self.client = None
        else:
            try:
                self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
                logger.info("TavilyService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {str(e)}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Tavily service is available."""
        return self.client is not None
    
    def search(
        self,
        query: str,
        max_results: int = 3,
        search_depth: str = "basic"
    ) -> List[WebSearchResult]:
        """
        Perform web search using Tavily API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 3)
            search_depth: "basic" or "advanced" (default: "basic")
        
        Returns:
            List of WebSearchResult objects
        
        Raises:
            ServiceUnavailableException: If Tavily API is unavailable or fails
        """
        if not self.is_available():
            logger.warning("Tavily service not available, returning empty results")
            raise ServiceUnavailableException(
                message="Web search is not configured",
                details={"reason": "TAVILY_API_KEY not set"}
            )
        
        logger.info(f"Performing web search (max_results={max_results})")
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=False,
                include_raw_content=False
            )
            
            results = []
            for result in response.get('results', []):
                try:
                    web_result = WebSearchResult(
                        title=result.get('title', 'Untitled'),
                        url=result.get('url', ''),
                        content=result.get('content', ''),
                        score=result.get('score')
                    )
                    results.append(web_result)
                except Exception as e:
                    logger.warning(f"Failed to parse Tavily result: {str(e)}")
                    continue
            
            logger.info(f"Web search completed: found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Tavily API error: {str(e)}")
            raise ServiceUnavailableException(
                message="Web search failed",
                details={"error": str(e), "query": query[:100]}
            )


# Singleton instance
_tavily_service_instance = None

def get_tavily_service() -> TavilyService:
    """Get or create singleton TavilyService instance."""
    global _tavily_service_instance
    if _tavily_service_instance is None:
        _tavily_service_instance = TavilyService()
    return _tavily_service_instance
