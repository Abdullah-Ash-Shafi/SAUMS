"""Course Registration and Advising API router."""
from typing import Sequence
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from suams.auth.dependencies import get_current_user, require_roles
from suams.database import get_db
from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.models.user import User, UserRole
from suams.notifications.publisher import (
    AcademicEvent,
    AcademicEventType,
    academic_publisher,
)
from suams.registration.service import RegistrationService
from suams.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseRegistrationRequest,
    EnrollmentResponse,
)

router = APIRouter(prefix="/registration", tags=["Course Registration & Advising"])


@router.get("/courses", response_model=list[CourseResponse])
def get_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Course]:
    """Retrieve the full semester course catalog."""
    return RegistrationService.get_course_catalog(db)


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate,
    current_user: User = Depends(require_roles(UserRole.DEPARTMENT_ADMIN)),
    db: Session = Depends(get_db),
) -> Course:
    """Create a new course in the catalog. Restricted to DepartmentAdmin."""
    return RegistrationService.create_course(course_in.model_dump(), db)


@router.post("/register", response_model=EnrollmentResponse)
def register_for_course(
    payload: CourseRegistrationRequest,
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> Enrollment:
    """Register the current student for a course.

    Validates prerequisites, seat capacity, and semester credit bounds (max 24 credits).
    Initializes advising status as PENDING.
    """
    return RegistrationService.register_course(
        student_id=current_user.id,
        course_id=payload.course_id,
        db=db,
    )


@router.get("/my-courses", response_model=list[EnrollmentResponse])
def get_my_courses(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
    db: Session = Depends(get_db),
) -> list[Enrollment]:
    """Retrieve all enrolled/registered courses for the logged-in student."""
    return RegistrationService.get_student_enrollments(student_id=current_user.id, db=db)


@router.get("/advisor/pending", response_model=list[EnrollmentResponse])
def get_pending_advising_queue(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.DEPARTMENT_ADMIN)),
    db: Session = Depends(get_db),
) -> list[Enrollment]:
    """Retrieve pending course registrations awaiting advisor review.

    Restricted to Teacher and DepartmentAdmin.
    """
    return RegistrationService.get_pending_enrollments(db)


@router.put("/advisor/approve/{enrollment_id}", response_model=EnrollmentResponse)
def approve_registration(
    enrollment_id: int,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.DEPARTMENT_ADMIN)),
    db: Session = Depends(get_db),
) -> Enrollment:
    """Approve a student's course registration.

    Transitions enrollment status: PENDING -> APPROVED.
    Restricted to Teacher and DepartmentAdmin.
    """
    try:
        enrollment = RegistrationService.update_enrollment_status(
            enrollment_id=enrollment_id,
            new_status=EnrollmentStatus.APPROVED,
            db=db,
        )
        recipient_email = (
            enrollment.student.email
            if enrollment.student and enrollment.student.email
            else f"student{enrollment.student_id}@ruet.ac.bd"
        )
        academic_publisher.notify(
            AcademicEvent(
                event_type=AcademicEventType.REGISTRATION_APPROVED,
                payload={
                    "user_id": enrollment.student_id,
                    "recipient": recipient_email,
                    "enrollment_id": enrollment.id,
                    "message": f"Your registration for course ID {enrollment.course_id} has been approved.",
                },
            ),
            db=db,
        )
        return enrollment
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/advisor/reject/{enrollment_id}", response_model=EnrollmentResponse)
def reject_registration(
    enrollment_id: int,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.DEPARTMENT_ADMIN)),
    db: Session = Depends(get_db),
) -> Enrollment:
    """Reject a student's course registration.

    Transitions enrollment status: PENDING -> REJECTED.
    Restricted to Teacher and DepartmentAdmin.
    """
    try:
        return RegistrationService.update_enrollment_status(
            enrollment_id=enrollment_id,
            new_status=EnrollmentStatus.REJECTED,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
