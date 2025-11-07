"""
Workflow model - stores workflow definitions created by users
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class Workflow(Base):
    """Workflow definition with graph structure (nodes + edges)"""

    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    config = Column(JSONB, nullable=False, default=dict)  # Stores {nodes: [], edges: []}
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(255), default="admin", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_workflow_name_version'),
    )

    def __repr__(self):
        return f"<Workflow(name='{self.name}', version={self.version})>"
