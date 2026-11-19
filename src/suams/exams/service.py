"""Exam Form Generation and Mark Evaluation Service.

Implements basis-path evaluated grading logic, attendance disqualification checks,
and semester exam form generation restricted strictly to APPROVED course enrollments.
"""
from typing import Sequence
from sqlalchemy.orm import Session

from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.models.exam import ExamForm
from suams.models.result import Result


def evaluateResult(is_enrolled: bool, attendance: float, total_marks: float) -> str:
    """Evaluate student course result based on enrollment, attendance, and total marks.

    White-Box Basis-Path Testing Design:
    Cyclomatic Complexity V(G) = 3 (predicates) + 1 = 4 Independent Paths:
      - Path 1 (TC-WB-01): Not enrolled -> 'NOT_ENROLLED'
      - Path 2 (TC-WB-02): Enrolled, attendance < 75.0 -> 'DISQUALIFIED'
      - Path 3 (TC-WB-03): Enrolled, attendance >= 75.0, total_marks >= 40.0 -> 'PASS'
      - Path 4 (TC-WB-04): Enrolled, attendance >= 75.0, total_marks < 40.0 -> 'FAIL'

    Args:
        is_enrolled: Boolean flag whether student has an enrollment record.
        attendance: Student's class attendance percentage (0.0 to 100.0).
        total_marks: Total score (Continuous Assessment + Final Exam).

    Returns:
        One of 'NOT_ENROLLED', 'DISQUALIFIED', 'PASS', or 'FAIL'.
    """
    if not is_enrolled:
        return "NOT_ENROLLED"
    elif attendance < 75.0:
        return "DISQUALIFIED"
    elif total_marks >= 40.0:
        return "PASS"
    else:
        return "FAIL"


class ExamService:
    """Service providing exam form clearance and teacher mark evaluation operations."""

    @staticmethod
    def generate_exam_form(
        student_id: int,
        semester: int,
        db: Session,
    ) -> tuple[ExamForm, list[Course]]:
        """Generate an exam form containing ONLY courses with APPROVED enrollment status.

        Args:
            student_id: ID of the student requesting the form.
            semester: Target academic semester.
            db: SQLAlchemy session.

        Returns:
            A tuple of (ExamForm model, list of cleared Course models).

        Raises:
            ValueError: If the student has zero APPROVED enrollments.
        """
        enrollments: Sequence[Enrollment] = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.APPROVED,
            )
            .all()
        )

        # Filter courses for this semester with strict APPROVED check
        approved_courses: list[Course] = [
            e.course
            for e in enrollments
            if e.status == EnrollmentStatus.APPROVED
            and e.course
            and (e.course.semester is None or e.course.semester == semester)
        ]

        if not approved_courses:
            raise ValueError(
                f"Cannot generate exam form: No approved course enrollments found for student {student_id} in semester {semester}."
            )

        exam_form = ExamForm(
            student_id=student_id,
            semester=semester,
            status="APPROVED",
        )
        db.add(exam_form)
        db.commit()
        db.refresh(exam_form)

        return exam_form, approved_courses

    @staticmethod
    def submit_marks(
        student_id: int,
        course_id: int,
        ca_marks: float,
        final_marks: float,
        db: Session,
    ) -> Result:
        """Process mark entry for Continuous Assessment (CA) and Final Exam.

        Continuous Assessment (CA) carries 40% weight (0 to 40 marks).
        Final Exam carries 60% weight (0 to 60 marks).

        Args:
            student_id: ID of the student.
            course_id: ID of the course.
            ca_marks: Score in CA (0.0 to 40.0).
            final_marks: Score in Final Exam (0.0 to 60.0).
            db: SQLAlchemy session.

        Returns:
            The created or updated Result record with evaluation status.

        Raises:
            ValueError: If CA marks or Final marks are outside valid ranges,
                        or student is not enrolled.
        """
        if ca_marks < 0.0 or ca_marks > 40.0:
            raise ValueError("Continuous Assessment (CA) marks must be between 0 and 40.")
        if final_marks < 0.0 or final_marks > 60.0:
            raise ValueError("Final Exam marks must be between 0 and 60.")

        enrollment: Enrollment | None = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
            .first()
        )

        if not enrollment:
            raise ValueError(
                f"Student {student_id} is not enrolled in course {course_id}."
            )

        is_enrolled = True
        attendance = enrollment.attendance
        total_marks = round(ca_marks + final_marks, 2)

        evaluation_status = evaluateResult(
            is_enrolled=is_enrolled,
            attendance=attendance,
            total_marks=total_marks,
        )

        # Check for existing Result record to update or create
        result: Result | None = (
            db.query(Result).filter(Result.enrollment_id == enrollment.id).first()
        )
        if not result:
            result = Result(
                enrollment_id=enrollment.id,
                student_id=student_id,
                course_id=course_id,
                ca_marks=ca_marks,
                final_marks=final_marks,
                total_marks=total_marks,
                evaluation_status=evaluation_status,
                is_published=False,
            )
            db.add(result)
        else:
            result.ca_marks = ca_marks
            result.final_marks = final_marks
            result.total_marks = total_marks
            result.evaluation_status = evaluation_status

        db.commit()
        db.refresh(result)
        return result
