"""Pydantic schemas for result publishing and grade viewing."""
from typing import Optional
from pydantic import BaseModel


class PublishResultRequest(BaseModel):
    """Schema for requesting result publication for a course."""

    course_id: int


class ResultResponse(BaseModel):
    """Schema for published course result."""

    id: int
    enrollment_id: int
    student_id: int
    course_id: int
    ca_marks: float
    final_marks: float
    total_marks: float
    grade: Optional[str] = None
    gpa: Optional[float] = None
    evaluation_status: Optional[str] = None
    is_published: bool

    model_config = {"from_attributes": True}
