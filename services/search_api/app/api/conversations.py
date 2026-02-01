"""
Conversation management endpoints.
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException

from app.models.conversation import (
    Conversation,
    ConversationListItem,
    ConversationDetail,
    DeleteConversationResponse
)
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat/conversations", tags=["conversations"])


@router.get("/", response_model=List[ConversationListItem])
def list_conversations():
    """
    List all conversations with basic metadata.
    
    Returns:
        List of conversations with ID, creation time, and message count
    """
    logger.info("Listing all conversations")
    
    try:
        conversation_service = ConversationService()
        conversations = conversation_service.list_conversations()
        
        logger.info(f"Found {len(conversations)} conversations")
        return conversations
    
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str):
    """
    Get a specific conversation with all messages.
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        Conversation with full message history
    """
    logger.info(f"Getting conversation: {conversation_id}")
    
    try:
        conversation_service = ConversationService()
        conversation = conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Conversation not found: {conversation_id}"
            )
        
        logger.info(f"Retrieved conversation {conversation_id} with {len(conversation.get('messages', []))} messages")
        
        # Convert to response model
        return ConversationDetail(
            conversation_id=conversation['conversation_id'],
            user_id=conversation.get('user_id'),
            messages=conversation.get('messages', []),
            created_at=conversation['created_at'],
            updated_at=conversation['updated_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.delete("/{conversation_id}", response_model=DeleteConversationResponse)
def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: Conversation ID to delete
    
    Returns:
        Deletion status
    """
    logger.info(f"Delete request for conversation: {conversation_id}")
    
    try:
        conversation_service = ConversationService()
        
        # Check if conversation exists
        conversation = conversation_service.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Conversation not found: {conversation_id}"
            )
        
        # Delete conversation
        success = conversation_service.delete_conversation(conversation_id)
        
        if success:
            logger.info(f"Successfully deleted conversation: {conversation_id}")
            return DeleteConversationResponse(
                conversation_id=conversation_id,
                deleted=True,
                message="Conversation deleted successfully"
            )
        else:
            logger.error(f"Failed to delete conversation: {conversation_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete conversation"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )
