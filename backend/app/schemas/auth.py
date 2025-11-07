"""
Pydantic schemas for Authentication endpoints
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for current user response"""
    username: str
