import logging
from fastapi import APIRouter, Depends

from app.models.conversation import ChatRequest, ChatResponse
from app.services.bedrock_service import get_bedrock_service
from app.services.conversation_service import ConversationService
from app.services.search_service import SearchService
from app.services.embedding_service import get_embedding_service
from app.services.tavily_service import get_tavily_service
from app.dependencies import get_vector_store
from app.core.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    vector_store=Depends(get_vector_store)
):
    logger.info(f"Chat request: conversation_id={request.conversation_id}, use_web_search={request.use_web_search}, top_k={request.top_k}")
    
    bedrock_service = get_bedrock_service()
    conversation_service = ConversationService()
    embedding_service = get_embedding_service()
    search_service = SearchService(embedding_service, vector_store)
    
    # Search documents
    logger.info(f"Searching for relevant chunks (top_k={request.top_k})")
    search_results = search_service.search(request.query, top_k=request.top_k)
    
    if not search_results:
        logger.warning("No relevant chunks found for query")
        context_chunks = []
    else:
        context_chunks = search_results
        logger.info(f"Found {len(context_chunks)} relevant chunks")
    
    # Web search (if enabled)
    web_results = []
    if request.use_web_search:
        logger.info("Web search enabled, fetching results from Tavily")
        tavily_service = get_tavily_service()
        
        if tavily_service.is_available():
            try:
                web_results = tavily_service.search(
                    query=request.query,
                    max_results=3
                )
                logger.info(f"Found {len(web_results)} web results")
            except ServiceUnavailableException as e:
                logger.warning(f"Web search failed: {e.message}, continuing without web results")
                # Continue without web results - graceful degradation
        else:
            logger.warning("Tavily service not available, skipping web search")
    
    # Get or create conversation
    if request.conversation_id:
        conversation_history = conversation_service.get_conversation_history(
            request.conversation_id,
            limit=10
        )
        conversation_id = request.conversation_id
        logger.info(f"Using existing conversation {conversation_id} with {len(conversation_history)} messages")
    else:
        conversation_id = conversation_service.create_conversation()
        conversation_history = []
        logger.info(f"Created new conversation {conversation_id}")
    
    # Generate answer with both document and web context
    logger.info("Generating answer with Bedrock")
    bedrock_response = bedrock_service.generate_answer(
        query=request.query,
        context_chunks=context_chunks,
        web_results=web_results,
        conversation_history=conversation_history
    )
    
    answer = bedrock_response['answer']
    model = bedrock_response['model']
    
    # Save conversation
    logger.info("Saving conversation history")
    conversation_service.add_message(conversation_id, 'user', request.query)
    conversation_service.add_message(conversation_id, 'assistant', answer)
    
    logger.info(f"Chat completed successfully (answer length: {len(answer)} chars)")
    
    # Combine sources from documents and web
    sources_dict = []
    
    # Add document sources
    for chunk in context_chunks:
        sources_dict.append({
            "type": "document",
            "document_id": chunk.document_id,
            "document_title": chunk.document_title,
            "content": chunk.content,
            "score": chunk.score
        })
    
    # Add web sources
    for web_result in web_results:
        sources_dict.append({
            "type": "web",
            "title": web_result.title,
            "url": web_result.url,
            "content": web_result.content,
            "score": web_result.score
        })
    
    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        sources=sources_dict,
        model=model
    )
