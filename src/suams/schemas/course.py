"""Pydantic schemas for courses and course registrations."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from suams.models.enrollment import EnrollmentStatus


class CourseBase(BaseModel):
    """Base schema for course attributes."""

    code: str
    title: str
    credits: float
    seat_capacity: int = 60
    department: Optional[str] = None
    semester: Optional[int] = None
    prerequisite_id: Optional[int] = None


class CourseCreate(CourseBase):
    """Schema for creating a course in the catalog."""

    pass


class CourseResponse(CourseBase):
    """Schema for course details returned to clients."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseRegistrationRequest(BaseModel):
    """Schema for submitting a course registration."""

    course_id: int


class EnrollmentResponse(BaseModel):
    """Schema for enrollment details and advising status."""

    id: int
    student_id: int
    course_id: int
    status: EnrollmentStatus
    attendance: float
    created_at: datetime
    course: Optional[CourseResponse] = None

    model_config = {"from_attributes": True}
