"""
Action model - stores available action blocks from the catalog
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Action(Base):
    """Action block available in the library"""

    __tablename__ = "actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)  # Human-readable name
    class_name = Column(String(255), nullable=False)
    method_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(500), nullable=False)
    http_method = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSONB, nullable=False, default=dict)
    returns = Column(JSONB, nullable=False, default=dict)
    category = Column(String(255), nullable=True, index=True)
    tags = Column(ARRAY(String), nullable=True, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Action(action_name='{self.action_name}', domain='{self.domain}')>"
