"""Results API router for result publishing and grade viewing."""
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from suams.auth.dependencies import require_roles
from suams.models.user import User, UserRole

router = APIRouter(prefix="/results", tags=["Results"])


class PublishResultRequest(BaseModel):
    """Payload for result publication."""

    course_id: int


@router.post("/publish")
def publish_results(
    payload: PublishResultRequest,
    current_user: User = Depends(require_roles(UserRole.EXAM_CONTROLLER)),
) -> dict[str, Any]:
    """Publish results for a course. Restricted exclusively to ExamController.

    Enforces RBAC: returns HTTP 403 Forbidden if accessed by Student, Teacher, or Admin.
    """
    return {
        "status": "success",
        "message": f"Results for course {payload.course_id} published successfully by controller {current_user.username}.",
        "course_id": payload.course_id,
        "published_by": current_user.username,
    }
