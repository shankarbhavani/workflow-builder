"""
Pydantic schemas for Execution endpoints
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class ExecutionLogResponse(BaseModel):
    """Schema for execution log response"""
    id: UUID
    execution_id: UUID
    step_name: str
    action_name: str
    status: str
    inputs: Optional[Dict[str, Any]]
    outputs: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionListItemResponse(BaseModel):
    """Schema for execution in list view (without logs)"""
    id: UUID
    workflow_id: UUID
    workflow_name: str
    temporal_workflow_id: str
    temporal_run_id: str
    status: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Schema for execution response with logs (detail view)"""
    id: UUID
    workflow_id: UUID
    workflow_name: str
    temporal_workflow_id: str
    temporal_run_id: str
    status: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    logs: List[ExecutionLogResponse] = []

    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Schema for paginated execution list"""
    executions: List[ExecutionListItemResponse]
    total: int
    skip: int
    limit: int


class ExecutionCancelResponse(BaseModel):
    """Schema for execution cancel response"""
    execution_id: UUID
    status: str
    message: str = "Execution cancelled successfully"
