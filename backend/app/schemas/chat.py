"""
Pydantic schemas for Chat endpoints
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class ChatMessage(BaseModel):
    """Schema for a single chat message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., description="User's message")
    session_id: Optional[UUID] = Field(None, description="Existing session ID (optional)")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    session_id: UUID = Field(..., description="Conversation session ID")
    response: str = Field(..., description="Assistant's response")
    workflow_draft: Optional[Dict[str, Any]] = Field(None, description="Current workflow draft")
    messages: List[ChatMessage] = Field(default_factory=list, description="Full conversation history")


class ConversationSessionResponse(BaseModel):
    """Schema for conversation session response"""
    id: UUID
    workflow_id: Optional[UUID]
    status: str
    messages: List[Dict[str, Any]]
    workflow_draft: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list"""
    sessions: List[ConversationSessionResponse]
    total: int
    skip: int
    limit: int
