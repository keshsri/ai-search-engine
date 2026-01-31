"""
Bedrock service for LLM-powered answer generation.
"""
import json
import logging
import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)


class BedrockService:
    """Service for interacting with AWS Bedrock LLMs."""
    
    def __init__(self):
        """Initialize Bedrock client."""
        self.client = boto3.client('bedrock-runtime', region_name=settings.AWS_REGION)
        self.model_id = settings.BEDROCK_MODEL_ID
        self.max_tokens = settings.BEDROCK_MAX_TOKENS
        self.temperature = settings.BEDROCK_TEMPERATURE
        logger.info(f"BedrockService initialized with model: {self.model_id}")
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate an answer using Bedrock LLM with RAG context.
        
        Args:
            query: User's question
            context_chunks: Retrieved document chunks for context
            conversation_history: Previous messages in conversation
        
        Returns:
            Dict with 'answer' and 'model' keys
        """
        logger.info(f"Generating answer for query: {query[:100]}...")
        
        # Build prompt with context
        prompt = self._build_prompt(query, context_chunks, conversation_history)
        
        # Call Bedrock
        try:
            response = self._invoke_model(prompt)
            logger.info(f"Successfully generated answer ({len(response['answer'])} chars)")
            return response
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            raise ServiceUnavailableException(
                message="Failed to generate answer from LLM",
                details={"error": str(e), "model": self.model_id}
            )
    
    def _build_prompt(
        self,
        query: str,
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Build the prompt with context and conversation history."""
        
        # Format context chunks
        context_text = "\n\n".join([
            f"[Document: {chunk.document_title}]\n{chunk.content}"
            for chunk in context_chunks
        ])
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = "User" if msg['role'] == 'user' else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
        
        # Construct full prompt
        prompt = f"""You are a helpful AI assistant that answers questions based on provided context.

Context from documents:
{context_text}
{history_text}

User question: {query}

Instructions:
- Answer the question based on the provided context
- If the context doesn't contain enough information, say so
- Be concise but complete
- Cite which document(s) you're referencing when relevant

Answer:"""
        
        logger.debug(f"Built prompt with {len(context_chunks)} chunks and {len(conversation_history or [])} history messages")
        return prompt
    
    def _invoke_model(self, prompt: str) -> Dict:
        """Invoke Bedrock model and return response."""
        
        # Prepare request body (Claude format)
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        logger.debug(f"Invoking Bedrock model: {self.model_id}")
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract answer from Claude response
            answer = response_body['content'][0]['text']
            
            return {
                'answer': answer,
                'model': self.model_id,
                'usage': response_body.get('usage', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock ClientError: {error_code} - {error_message}")
            
            if error_code == 'AccessDeniedException':
                raise ServiceUnavailableException(
                    message="Access denied to Bedrock model. Please check model access permissions.",
                    details={"model": self.model_id, "error": error_message}
                )
            elif error_code == 'ThrottlingException':
                raise ServiceUnavailableException(
                    message="Bedrock API rate limit exceeded. Please try again later.",
                    details={"model": self.model_id}
                )
            else:
                raise ServiceUnavailableException(
                    message=f"Bedrock API error: {error_message}",
                    details={"model": self.model_id, "error_code": error_code}
                )
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {str(e)}")
            raise


# Singleton instance
_bedrock_service_instance = None

def get_bedrock_service() -> BedrockService:
    """Get or create singleton BedrockService instance."""
    global _bedrock_service_instance
    if _bedrock_service_instance is None:
        _bedrock_service_instance = BedrockService()
    return _bedrock_service_instance
