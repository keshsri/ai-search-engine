"""
Conversation service for managing chat history in DynamoDB.
"""
import uuid
import logging
from typing import List, Dict, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.models.conversation import Message, Conversation

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation history."""
    
    def __init__(self):
        """Initialize DynamoDB client."""
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(settings.CONVERSATIONS_TABLE_NAME)
        logger.info(f"ConversationService initialized with table: {settings.CONVERSATIONS_TABLE_NAME}")
    
    def create_conversation(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            user_id: Optional user identifier
        
        Returns:
            conversation_id: New conversation ID
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Calculate TTL: 15 days from now (in Unix timestamp)
        import time
        ttl = int(time.time()) + (15 * 24 * 60 * 60)  # 15 days in seconds
        
        try:
            self.table.put_item(
                Item={
                    'conversation_id': conversation_id,
                    'user_id': user_id or 'anonymous',
                    'messages': [],
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    'ttl': ttl  # Auto-delete after 15 days
                }
            )
            logger.info(f"Created conversation: {conversation_id} with TTL={ttl}")
            return conversation_id
        except ClientError as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise DatabaseException(
                message="Failed to create conversation",
                details={"error": str(e)}
            )
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """
        Add a message to conversation.
        
        Args:
            conversation_id: Conversation ID
            role: 'user' or 'assistant'
            content: Message content
        """
        timestamp = datetime.utcnow().isoformat()
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp
        }
        
        try:
            self.table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression='SET messages = list_append(if_not_exists(messages, :empty_list), :message), updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':message': [message],
                    ':timestamp': timestamp,
                    ':empty_list': []
                }
            )
            logger.debug(f"Added {role} message to conversation {conversation_id}")
        except ClientError as e:
            logger.error(f"Failed to add message to conversation: {str(e)}")
            raise DatabaseException(
                message="Failed to add message to conversation",
                details={"conversation_id": conversation_id, "error": str(e)}
            )
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            Conversation data or None if not found
        """
        try:
            response = self.table.get_item(
                Key={'conversation_id': conversation_id}
            )
            
            if 'Item' in response:
                logger.debug(f"Retrieved conversation {conversation_id} with {len(response['Item'].get('messages', []))} messages")
                return response['Item']
            else:
                logger.warning(f"Conversation not found: {conversation_id}")
                return None
                
        except ClientError as e:
            logger.error(f"Failed to get conversation: {str(e)}")
            raise DatabaseException(
                message="Failed to retrieve conversation",
                details={"conversation_id": conversation_id, "error": str(e)}
            )
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """
        Get conversation message history.
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
        
        Returns:
            List of messages
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return []
        
        messages = conversation.get('messages', [])
        
        # Return last N messages
        return messages[-limit:] if len(messages) > limit else messages
    
    def list_conversations(self) -> List[Dict]:
        """
        List all conversations with basic metadata.
        
        Returns:
            List of conversations with ID, message count, and timestamps
        """
        try:
            response = self.table.scan()
            conversations = response.get('Items', [])
            
            # Format response
            result = []
            for conv in conversations:
                # Handle missing fields gracefully
                created_at = conv.get('created_at', datetime.utcnow().isoformat())
                updated_at = conv.get('updated_at', created_at)
                
                result.append({
                    'conversation_id': conv['conversation_id'],
                    'user_id': conv.get('user_id', 'anonymous'),
                    'message_count': len(conv.get('messages', [])),
                    'created_at': created_at,
                    'updated_at': updated_at
                })
            
            # Sort by updated_at (most recent first)
            result.sort(key=lambda x: x['updated_at'], reverse=True)
            
            logger.info(f"Listed {len(result)} conversations")
            return result
            
        except ClientError as e:
            logger.error(f"Failed to list conversations: {str(e)}")
            raise DatabaseException(
                message="Failed to list conversations",
                details={"error": str(e)}
            )
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID to delete
        
        Returns:
            True if deleted successfully
        """
        try:
            self.table.delete_item(
                Key={'conversation_id': conversation_id}
            )
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete conversation: {str(e)}")
            raise DatabaseException(
                message="Failed to delete conversation",
                details={"conversation_id": conversation_id, "error": str(e)}
            )
