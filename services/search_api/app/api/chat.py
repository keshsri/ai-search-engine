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
    logger.info(f"Chat request: query='{request.query[:50]}...', conversation_id={request.conversation_id}")
    
    bedrock_service = get_bedrock_service()
    conversation_service = ConversationService()
    embedding_service = get_embedding_service()
    search_service = SearchService(embedding_service, vector_store)
    
    logger.info(f"Searching for relevant chunks (top_k={request.top_k})")
    search_results = search_service.search(request.query, top_k=request.top_k)
    
    if not search_results:
        logger.warning("No relevant chunks found for query")
        context_chunks = []
    else:
        context_chunks = search_results
        logger.info(f"Found {len(context_chunks)} relevant chunks")
    
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
    
    logger.info("Generating answer with Bedrock")
    bedrock_response = bedrock_service.generate_answer(
        query=request.query,
        context_chunks=context_chunks,
        conversation_history=conversation_history
    )
    
    answer = bedrock_response['answer']
    model = bedrock_response['model']
    
    logger.info("Saving conversation history")
    conversation_service.add_message(conversation_id, 'user', request.query)
    conversation_service.add_message(conversation_id, 'assistant', answer)
    
    logger.info(f"Chat completed successfully (answer length: {len(answer)} chars)")
    
    sources_dict = [
        {
            "document_id": chunk.document_id,
            "document_title": chunk.document_title,
            "content": chunk.content,
            "score": chunk.score
        }
        for chunk in context_chunks
    ]
    
    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        sources=sources_dict,
        model=model
    )
