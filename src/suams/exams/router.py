"""Exams API router for evaluation and exam form endpoints."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from suams.auth.dependencies import require_roles
from suams.database import get_db
from suams.exams.service import ExamService
from suams.models.result import Result
from suams.models.user import User, UserRole
from suams.schemas.exam import (
    ExamFormGenerateRequest,
    ExamFormResponse,
    MarkEntryRequest,
    MarkEntryResponse,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("/teacher/evaluation-queue")
def get_teacher_evaluation_queue(
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
) -> dict[str, Any]:
    """Protected endpoint for teachers to access continuous assessment and mark entry queue.

    Enforces RBAC: returns HTTP 403 Forbidden if accessed by non-Teacher roles.
    """
    return {
        "status": "success",
        "message": f"Welcome Professor {current_user.full_name}, your evaluation queue is ready.",
        "queue": [],
    }


@router.post("/form/generate", response_model=ExamFormResponse)
def generate_exam_form(
    payload: ExamFormGenerateRequest,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate an exam form for the requesting student.

    Strictly ensures only courses with APPROVED enrollment status appear on the form.
    Restricted to Student role.
    """
    try:
        exam_form, approved_courses = ExamService.generate_exam_form(
            student_id=current_user.id,
            semester=payload.semester,
            db=db,
        )
        return {
            "id": exam_form.id,
            "student_id": exam_form.student_id,
            "semester": exam_form.semester,
            "status": exam_form.status,
            "approved_courses": approved_courses,
            "created_at": exam_form.created_at,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/marks/entry", response_model=MarkEntryResponse)
def enter_marks(
    payload: MarkEntryRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> Result:
    """Submit Continuous Assessment (CA, 40%) and Final Exam (60%) marks.

    Evaluates the result using white-box basis-path evaluated evaluateResult().
    Restricted to Teacher role.
    """
    try:
        return ExamService.submit_marks(
            student_id=payload.student_id,
            course_id=payload.course_id,
            ca_marks=payload.ca_marks,
            final_marks=payload.final_marks,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
