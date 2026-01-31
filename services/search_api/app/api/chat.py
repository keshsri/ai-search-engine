"""
Chat endpoint for RAG-powered question answering.
"""
import logging
from fastapi import APIRouter, Depends

from app.models.conversation import ChatRequest, ChatResponse
from app.services.bedrock_service import get_bedrock_service
from app.services.conversation_service import ConversationService
from app.services.search_service import SearchService
from app.services.embedding_service import get_embedding_service
from app.dependencies import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    vector_store=Depends(get_vector_store)
):
    """
    Chat endpoint with RAG (Retrieval-Augmented Generation).
    
    Flow:
    1. Retrieve relevant document chunks (semantic search)
    2. Get conversation history (if conversation_id provided)
    3. Generate answer using Bedrock LLM with context
    4. Save conversation history
    5. Return answer with sources
    """
    logger.info(f"Chat request: query='{request.query[:50]}...', conversation_id={request.conversation_id}")
    
    # Initialize services
    bedrock_service = get_bedrock_service()
    conversation_service = ConversationService()
    embedding_service = get_embedding_service()
    search_service = SearchService(embedding_service, vector_store)
    
    # Step 1: Retrieve relevant chunks
    logger.info(f"Searching for relevant chunks (top_k={request.top_k})")
    search_results = search_service.search(request.query, top_k=request.top_k)
    
    if not search_results:
        logger.warning("No relevant chunks found for query")
        # Return a response even if no context found
        context_chunks = []
    else:
        context_chunks = search_results
        logger.info(f"Found {len(context_chunks)} relevant chunks")
    
    # Step 2: Get or create conversation
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
    
    # Step 3: Generate answer with Bedrock
    logger.info("Generating answer with Bedrock")
    bedrock_response = bedrock_service.generate_answer(
        query=request.query,
        context_chunks=context_chunks,
        conversation_history=conversation_history
    )
    
    answer = bedrock_response['answer']
    model = bedrock_response['model']
    
    # Step 4: Save conversation
    logger.info("Saving conversation history")
    conversation_service.add_message(conversation_id, 'user', request.query)
    conversation_service.add_message(conversation_id, 'assistant', answer)
    
    # Step 5: Return response
    logger.info(f"Chat completed successfully (answer length: {len(answer)} chars)")
    
    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        sources=context_chunks,
        model=model
    )
