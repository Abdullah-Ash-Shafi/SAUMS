"""Enrollment model representing student course registrations."""
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from suams.database import Base


class EnrollmentStatus(str, Enum):
    """Enumeration of enrollment / advising statuses."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Enrollment(Base):
    """SQLAlchemy model representing a course enrollment record."""

    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    status: Mapped[EnrollmentStatus] = mapped_column(
        String(20), default=EnrollmentStatus.PENDING, nullable=False
    )
    attendance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student: Mapped["User"] = relationship("User", backref="enrollments")  # type: ignore[name-defined] # noqa: F821
    course: Mapped["Course"] = relationship("Course", backref="enrollments")  # type: ignore[name-defined] # noqa: F821
