"""
Execution models - tracks workflow execution instances and logs
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Execution(Base):
    """Workflow execution instance"""

    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    temporal_workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    temporal_run_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # RUNNING, COMPLETED, FAILED, CANCELLED
    inputs = Column(JSONB, nullable=False, default=dict)
    outputs = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationship to logs
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Execution(id='{self.id}', status='{self.status}')>"


class ExecutionLog(Base):
    """Step-by-step execution logs"""

    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id"), nullable=False, index=True)
    step_name = Column(String(255), nullable=False)  # Node ID or step identifier
    action_name = Column(String(255), nullable=False)  # Which action was executed
    status = Column(String(50), nullable=False)  # SUCCESS, FAILED, SKIPPED
    inputs = Column(JSONB, nullable=True)
    outputs = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to execution
    execution = relationship("Execution", back_populates="logs")

    def __repr__(self):
        return f"<ExecutionLog(step_name='{self.step_name}', status='{self.status}')>"
