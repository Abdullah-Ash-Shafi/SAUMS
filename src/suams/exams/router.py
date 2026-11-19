"""Exams API router for evaluation and exam form endpoints."""
from typing import Any
from fastapi import APIRouter, Depends
from suams.auth.dependencies import require_roles
from suams.models.user import User, UserRole

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
