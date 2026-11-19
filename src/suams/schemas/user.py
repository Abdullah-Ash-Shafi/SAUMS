"""Pydantic schemas for users and dashboard payloads."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr
from suams.models.user import UserRole


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    semester: Optional[int] = None


class UserCreate(UserBase):
    """Schema for registering a new user."""

    password: str


class UserResponse(UserBase):
    """Schema for returning user information."""

    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BaseDashboard(BaseModel):
    """Base schema for all role-specific dashboards."""

    user_id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    menu_items: list[str]
    additional_data: dict[str, Any] = {}
