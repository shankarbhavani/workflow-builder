"""
Pydantic schemas for Action endpoints
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class ActionBase(BaseModel):
    """Base action schema"""
    action_name: str
    display_name: Optional[str] = None
    class_name: str
    method_name: str
    domain: str
    endpoint: str
    http_method: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    returns: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class ActionCreate(ActionBase):
    """Schema for creating an action"""
    pass


class ActionUpdate(BaseModel):
    """Schema for updating an action"""
    action_name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ActionResponse(ActionBase):
    """Schema for action response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionListResponse(BaseModel):
    """Schema for paginated action list"""
    actions: List[ActionResponse]
    total: int
    skip: int
    limit: int
