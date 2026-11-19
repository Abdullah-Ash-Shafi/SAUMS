"""Pydantic schemas for authentication and tokens."""
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Schema for user login credentials."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for access token response."""

    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class TokenData(BaseModel):
    """Schema for decoded token payload."""

    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
