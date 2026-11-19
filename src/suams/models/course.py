"""Course model representing academic courses in the catalog."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from suams.database import Base


class Course(Base):
    """SQLAlchemy model representing a course."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[float] = mapped_column(Float, nullable=False)
    seat_capacity: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prerequisite_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    prerequisite: Mapped[Optional["Course"]] = relationship(
        "Course", remote_side=[id], backref="dependent_courses"
    )
