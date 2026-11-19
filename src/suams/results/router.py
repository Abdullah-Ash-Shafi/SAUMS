"""Results API router for result publishing and grade viewing."""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from suams.auth.dependencies import require_roles
from suams.database import get_db
from suams.models.result import Result
from suams.models.user import User, UserRole
from suams.results.service import ResultService
from suams.schemas.result import PublishResultRequest, ResultResponse

router = APIRouter(prefix="/results", tags=["Results"])


@router.post("/publish")
def publish_results(
    payload: PublishResultRequest,
    current_user: User = Depends(require_roles(UserRole.EXAM_CONTROLLER)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Publish results for a course. Restricted exclusively to ExamController.

    Calculates GPA and grades via the Strategy Pattern, marks results as published,
    and dispatches academic notifications via the Observer Pattern.
    """
    published_results = ResultService.publish_course_results(
        course_id=payload.course_id,
        db=db,
    )
    return {
        "status": "success",
        "message": f"Results for course {payload.course_id} published successfully by controller {current_user.username}.",
        "course_id": payload.course_id,
        "published_count": len(published_results),
        "published_by": current_user.username,
    }


@router.get("/my-results", response_model=list[ResultResponse])
def get_my_results(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> list[Result]:
    """Retrieve published results and GPA for the currently logged-in student."""
    return ResultService.get_student_results(
        student_id=current_user.id,
        db=db,
    )
