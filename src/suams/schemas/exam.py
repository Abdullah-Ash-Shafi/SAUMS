"""Pydantic schemas for exam forms, evaluation, and mark entries."""
from datetime import datetime
from pydantic import BaseModel, Field
from suams.schemas.course import CourseResponse


class ExamFormGenerateRequest(BaseModel):
    """Schema for requesting exam form generation."""

    semester: int = Field(..., ge=1, le=12, description="Target semester number")


class ExamFormResponse(BaseModel):
    """Schema for generated exam form and cleared eligible courses."""

    id: int
    student_id: int
    semester: int
    status: str
    approved_courses: list[CourseResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkEntryRequest(BaseModel):
    """Schema for teacher mark submission."""

    student_id: int
    course_id: int
    ca_marks: float = Field(..., ge=0.0, le=40.0, description="Continuous assessment marks (0-40)")
    final_marks: float = Field(..., ge=0.0, le=60.0, description="Final exam marks (0-60)")


class MarkEntryResponse(BaseModel):
    """Schema returned after mark entry and evaluation."""

    id: int
    enrollment_id: int
    student_id: int
    course_id: int
    ca_marks: float
    final_marks: float
    total_marks: float
    evaluation_status: str
    is_published: bool

    model_config = {"from_attributes": True}
