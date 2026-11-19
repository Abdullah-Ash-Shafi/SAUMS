"""Course Registration and Advising Service.

Enforces business rules for credit loads (12 to 24 credits inclusive),
prerequisite verification, seat capacity management, and the advisor
approval workflow (PENDING -> APPROVED / REJECTED).
"""
from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus


def checkCreditLimit(
    student_id: int,
    new_course_credits: float,
    db: Session | None = None,
    current_credits: float | None = None,
) -> bool:
    """Enforce valid semester credit load between 12 and 24 credits (inclusive).

    Boundary-Value Analysis (BVA):
        - 11 credits: Invalid (< 12) -> False
        - 12 credits: Valid (Minimum boundary) -> True
        - 24 credits: Valid (Maximum boundary) -> True
        - 25 credits: Invalid (> 24) -> False

    Args:
        student_id: Primary key of the student.
        new_course_credits: Credit value of the course being evaluated or added.
        db: Optional database session to calculate student's current semester credits.
        current_credits: Optional direct override of student's current registered credits.

    Returns:
        True if the total credits fall within [12.0, 24.0] inclusive, False otherwise.
    """
    if current_credits is not None:
        total = current_credits + new_course_credits
    elif db is not None:
        enrollments: Sequence[Enrollment] = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status.in_([EnrollmentStatus.APPROVED, EnrollmentStatus.PENDING]),
            )
            .all()
        )
        existing = sum(
            e.course.credits for e in enrollments if e.course and e.course.credits is not None
        )
        total = existing + new_course_credits
    else:
        total = new_course_credits

    return 12.0 <= total <= 24.0


def check_seat_capacity(course_id: int, db: Session) -> bool:
    """Check if open seats are available for registration in a course.

    Args:
        course_id: Primary key of the course.
        db: SQLAlchemy session.

    Returns:
        True if currently enrolled + pending count < course.seat_capacity, False if full.

    Raises:
        ValueError: If course does not exist.
    """
    course: Course | None = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError(f"Course not found: ID {course_id}")

    enrolled_count: int = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.status.in_([EnrollmentStatus.APPROVED, EnrollmentStatus.PENDING]),
        )
        .count()
    )
    return enrolled_count < course.seat_capacity


def check_prerequisites(student_id: int, course_id: int, db: Session) -> bool:
    """Verify that all prerequisite courses have been completed and approved.

    Args:
        student_id: Primary key of the student.
        course_id: Primary key of the course to be registered.
        db: SQLAlchemy session.

    Returns:
        True if no prerequisite exists or prerequisite is completed with APPROVED status;
        False otherwise.

    Raises:
        ValueError: If course does not exist.
    """
    course: Course | None = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError(f"Course not found: ID {course_id}")

    if course.prerequisite_id is None:
        return True

    prereq_enrollment: Enrollment | None = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course.prerequisite_id,
            Enrollment.status == EnrollmentStatus.APPROVED,
        )
        .first()
    )
    return prereq_enrollment is not None


class RegistrationService:
    """Service handling course catalog management, registration, and advising workflows."""

    @staticmethod
    def get_course_catalog(db: Session) -> list[Course]:
        """Retrieve all active courses in the catalog."""
        return list(db.query(Course).all())

    @staticmethod
    def create_course(course_data: dict, db: Session) -> Course:
        """Create a new course in the catalog."""
        course = Course(**course_data)
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def register_course(student_id: int, course_id: int, db: Session) -> Enrollment:
        """Register a student for a course, enforcing prerequisites, seats, and load bounds.

        Args:
            student_id: ID of the registering student.
            course_id: ID of the target course.
            db: SQLAlchemy session.

        Returns:
            The created Enrollment instance with status PENDING.

        Raises:
            HTTPException (400): If duplicate registration, prerequisite missing,
                                 capacity exceeded, or maximum credit load surpassed.
            HTTPException (404): If course does not exist.
        """
        course: Course | None = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

        # Check for existing registration
        existing = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already registered for this course.",
            )

        # Check prerequisites
        if not check_prerequisites(student_id=student_id, course_id=course_id, db=db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prerequisite course {course.prerequisite_id} has not been completed.",
            )

        # Check seat capacity
        if not check_seat_capacity(course_id=course_id, db=db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course {course.code} is full: Seat capacity reached.",
            )

        # Check maximum credit limit (cannot exceed 24.0)
        current_enrollments = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status.in_([EnrollmentStatus.APPROVED, EnrollmentStatus.PENDING]),
            )
            .all()
        )
        total_credits = sum(e.course.credits for e in current_enrollments if e.course) + course.credits
        if total_credits > 24.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Credit limit exceeded: Adding {course.credits} credits totals {total_credits} (Max: 24.0).",
            )

        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.PENDING,
            attendance=0.0,
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def update_enrollment_status(
        enrollment_id: int,
        new_status: EnrollmentStatus,
        db: Session,
    ) -> Enrollment:
        """Update an enrollment record's advising status (PENDING -> APPROVED / REJECTED).

        Args:
            enrollment_id: ID of the enrollment record.
            new_status: Target status (EnrollmentStatus.APPROVED or REJECTED).
            db: SQLAlchemy session.

        Returns:
            The updated Enrollment record.

        Raises:
            ValueError: If the enrollment record is not found.
        """
        enrollment: Enrollment | None = (
            db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
        )
        if not enrollment:
            raise ValueError(f"Enrollment not found: ID {enrollment_id}")

        enrollment.status = new_status
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def get_student_enrollments(student_id: int, db: Session) -> list[Enrollment]:
        """Retrieve all course enrollments for a given student."""
        return list(
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .order_by(Enrollment.id.desc())
            .all()
        )

    @staticmethod
    def get_pending_enrollments(db: Session) -> list[Enrollment]:
        """Retrieve all enrollments currently awaiting advisor approval."""
        return list(
            db.query(Enrollment)
            .filter(Enrollment.status == EnrollmentStatus.PENDING)
            .order_by(Enrollment.id.asc())
            .all()
        )
