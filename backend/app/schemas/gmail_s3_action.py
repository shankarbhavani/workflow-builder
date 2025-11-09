"""
Schemas for Gmail to S3 action
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List
from datetime import datetime


class GmailConfig(BaseModel):
    """Gmail configuration"""
    gmail_email: str = Field(..., description="Gmail email address")
    gmail_app_password: str = Field(..., description="Gmail app password (not regular password)")
    time_range_start: Optional[str] = Field(None, description="Start time for email search (ISO format)")
    time_range_end: Optional[str] = Field(None, description="End time for email search (ISO format)")
    s3_folder: str = Field("bhavani", description="S3 folder path for uploads")
    test_mode: bool = Field(False, description="Enable test mode with mock data (bypasses Gmail/S3)")


class EventData(BaseModel):
    """Event data common to all actions"""
    shipper_id: str = Field(..., description="Shipper identifier")
    agent_id: str = Field(..., description="Agent identifier (e.g., TRACY, SAM)")
    parent_request_id: Optional[str] = Field(None, description="Parent request ID for tracking")
    workflow_id: Optional[str] = Field(None, description="Workflow ID")


class GmailS3ActionRequest(BaseModel):
    """Request schema for Gmail to S3 action"""
    event_data: EventData
    configurations: GmailConfig


class GmailS3ActionResponse(BaseModel):
    """Response schema for Gmail to S3 action"""
    data: Dict[str, Any] = Field(..., description="Response data")
    audit: List[dict] = Field(default_factory=list, description="Audit trail")


class AttachmentsData(BaseModel):
    """Data structure for attachments response"""
    attachments: Dict[str, str] = Field(
        ...,
        description="Dictionary mapping filename to presigned S3 URL"
    )
    processed_emails: int = Field(..., description="Number of emails processed")
    total_attachments: int = Field(..., description="Total number of PDF attachments downloaded")
    s3_bucket: str = Field(..., description="S3 bucket name where files were uploaded")
    s3_folder: str = Field(..., description="S3 folder path")
