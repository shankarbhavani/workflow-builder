"""
Conversation model - stores chat sessions for natural language workflow generation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConversationSession(Base):
    """Conversation session for natural language workflow creation"""

    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True)

    # JSONB fields
    messages = Column(JSONB, nullable=False, default=list)  # [{role, content, timestamp}]
    workflow_draft = Column(JSONB, nullable=True, default=dict)  # Current workflow structure

    # Status tracking
    status = Column(String(50), default="active", nullable=False)  # active, completed, abandoned

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    workflow = relationship("Workflow", backref="conversation_sessions", foreign_keys=[workflow_id])

    def __repr__(self):
        return f"<ConversationSession(id='{self.id}', status='{self.status}')>"
