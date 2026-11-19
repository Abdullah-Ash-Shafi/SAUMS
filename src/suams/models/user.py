"""User model and role definitions for RBAC."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from suams.database import Base


class UserRole(str, Enum):
    """Enumeration of user roles in the academic management system."""

    STUDENT = "Student"
    TEACHER = "Teacher"
    DEPARTMENT_ADMIN = "DepartmentAdmin"
    EXAM_CONTROLLER = "ExamController"


class User(Base):
    """SQLAlchemy model representing a user in SUAMS."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
