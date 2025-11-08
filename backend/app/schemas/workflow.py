"""
Pydantic schemas for Workflow endpoints
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class WorkflowNode(BaseModel):
    """Schema for a workflow node"""
    id: str
    type: str = "action"  # action, condition, loop
    data: Dict[str, Any]
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})


class WorkflowEdge(BaseModel):
    """Schema for a workflow edge"""
    id: str
    source: str
    target: str
    type: str = "default"  # default, conditional
    label: Optional[str] = None


class WorkflowConfig(BaseModel):
    """Schema for workflow configuration"""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]


class WorkflowBase(BaseModel):
    """Base workflow schema"""
    name: str
    description: Optional[str] = None
    config: WorkflowConfig


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow"""
    pass


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[WorkflowConfig] = None


class WorkflowResponse(BaseModel):
    """Schema for workflow response"""
    id: UUID
    name: str
    description: Optional[str]
    version: int
    config: Dict[str, Any]
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Schema for paginated workflow list"""
    workflows: List[WorkflowResponse]
    total: int
    skip: int
    limit: int


class WorkflowExecuteRequest(BaseModel):
    """Schema for workflow execution request"""
    inputs: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecuteResponse(BaseModel):
    """Schema for workflow execution response"""
    execution_id: UUID
    temporal_workflow_id: str
    status: str
    message: str = "Workflow execution started"


class WorkflowSuggestMetadataRequest(BaseModel):
    """Schema for AI metadata suggestion request"""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]


class WorkflowSuggestMetadataResponse(BaseModel):
    """Schema for AI metadata suggestion response"""
    title: str
    description: str
