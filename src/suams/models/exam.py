"""ExamForm model representing semester exam clearance forms."""
from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from suams.database import Base


class ExamForm(Base):
    """SQLAlchemy model representing an exam form."""

    __tablename__ = "exam_forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="APPROVED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    student: Mapped["User"] = relationship("User", backref="exam_forms")  # type: ignore[name-defined] # noqa: F821
