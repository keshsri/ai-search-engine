"""
Conversation models for chat history.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Message(BaseModel):
    """Single message in a conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class Conversation(BaseModel):
    """Conversation with message history."""
    conversation_id: str = Field(..., description="Unique conversation ID")
    user_id: Optional[str] = Field(None, description="User ID (optional)")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    query: str = Field(..., description="User's question", min_length=1)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for follow-up questions")
    top_k: int = Field(5, description="Number of context chunks to retrieve", ge=1, le=10)


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    answer: str = Field(..., description="Generated answer")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[dict] = Field(..., description="Source chunks used for context")
    model: str = Field(..., description="Model used for generation")
