"""Result model representing continuous assessment, final exam marks, and calculated grades."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from suams.database import Base


class Result(Base):
    """SQLAlchemy model representing an evaluation/result record."""

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enrollment_id: Mapped[int] = mapped_column(Integer, ForeignKey("enrollments.id"), nullable=False, unique=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    ca_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluation_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    enrollment: Mapped["Enrollment"] = relationship("Enrollment", backref="result")  # type: ignore[name-defined] # noqa: F821
    student: Mapped["User"] = relationship("User", backref="results")  # type: ignore[name-defined] # noqa: F821
    course: Mapped["Course"] = relationship("Course", backref="results")  # type: ignore[name-defined] # noqa: F821
