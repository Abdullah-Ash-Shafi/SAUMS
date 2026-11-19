"""Result processing service coordinating grading strategies and event publication."""
from typing import Sequence
from sqlalchemy.orm import Session

from suams.models.result import Result
from suams.notifications.publisher import (
    AcademicEvent,
    AcademicEventType,
    AcademicEventPublisher,
    academic_publisher,
)
from suams.results.grading import GradingStrategy, calculateGPA


class ResultService:
    """Service providing result calculation, publication, and student grade views."""

    @staticmethod
    def publish_course_results(
        course_id: int,
        db: Session,
        publisher: AcademicEventPublisher | None = None,
        strategy: GradingStrategy | None = None,
    ) -> list[Result]:
        """Publish all evaluated results for a specified course.

        Computes letter grades and GPAs using the configured Strategy Pattern,
        updates published state, and notifies observers via the Observer Pattern.

        Args:
            course_id: Target course identifier.
            db: SQLAlchemy session.
            publisher: Optional event publisher (defaults to academic_publisher).
            strategy: Optional grading strategy (defaults to StandardRUETGradingStrategy).

        Returns:
            List of published Result entities.
        """
        pub = publisher or academic_publisher
        results: Sequence[Result] = (
            db.query(Result).filter(Result.course_id == course_id).all()
        )

        for result in results:
            if result.evaluation_status == "DISQUALIFIED":
                grade, gpa = "F", 0.00
            else:
                grade, gpa = calculateGPA(
                    ca_marks=result.ca_marks,
                    final_marks=result.final_marks,
                    strategy=strategy,
                )

            result.grade = grade
            result.gpa = gpa
            result.is_published = True

            # Trigger Observer notification
            recipient_email = (
                result.student.email
                if result.student and result.student.email
                else f"student{result.student_id}@ruet.ac.bd"
            )
            event = AcademicEvent(
                event_type=AcademicEventType.RESULT_PUBLISHED,
                payload={
                    "user_id": result.student_id,
                    "recipient": recipient_email,
                    "course_id": course_id,
                    "message": f"Your final result for course ID {course_id} is published: Grade {grade}, GPA {gpa:.2f}.",
                },
            )
            pub.notify(event, db=db)

        db.commit()
        for r in results:
            db.refresh(r)
        return list(results)

    @staticmethod
    def get_student_results(student_id: int, db: Session) -> list[Result]:
        """Retrieve all published results for a student. Unpublished results are excluded."""
        return list(
            db.query(Result)
            .filter(
                Result.student_id == student_id,
                Result.is_published == True,  # noqa: E712
            )
            .all()
        )
