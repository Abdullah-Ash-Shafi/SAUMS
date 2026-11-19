"""Unit tests for SQLAlchemy database models and session setup."""
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from suams.database import Base, get_db
from suams.models.user import User, UserRole
from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.models.exam import ExamForm
from suams.models.result import Result
from suams.models.notification import NotificationLog


@pytest.fixture
def in_memory_db() -> Session:
    """Create an in-memory SQLite database session for unit testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user_model(in_memory_db: Session) -> None:
    """Test creating and querying a User model."""
    user = User(
        email="student@ruet.ac.bd",
        username="student1",
        full_name="John Doe",
        hashed_password="hashed_pw_test",
        role=UserRole.STUDENT,
        department="CSE",
        semester=5,
        is_active=True,
    )
    in_memory_db.add(user)
    in_memory_db.commit()
    in_memory_db.refresh(user)

    assert user.id is not None
    assert user.email == "student@ruet.ac.bd"
    assert user.role == UserRole.STUDENT
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)


def test_create_course_model(in_memory_db: Session) -> None:
    """Test creating and querying a Course model."""
    prereq = Course(
        code="CSE 1101",
        title="Intro to Programming",
        credits=3.0,
        seat_capacity=60,
        department="CSE",
        semester=1,
    )
    in_memory_db.add(prereq)
    in_memory_db.commit()
    in_memory_db.refresh(prereq)

    course = Course(
        code="CSE 2101",
        title="Data Structures",
        credits=3.0,
        seat_capacity=50,
        department="CSE",
        semester=3,
        prerequisite_id=prereq.id,
    )
    in_memory_db.add(course)
    in_memory_db.commit()
    in_memory_db.refresh(course)

    assert course.id is not None
    assert course.code == "CSE 2101"
    assert course.prerequisite_id == prereq.id
    assert course.seat_capacity == 50


def test_create_enrollment_model(in_memory_db: Session) -> None:
    """Test creating an Enrollment model."""
    user = User(
        email="student2@ruet.ac.bd",
        username="student2",
        full_name="Alice Smith",
        hashed_password="pw",
        role=UserRole.STUDENT,
    )
    course = Course(
        code="CSE 3206",
        title="Software Engineering",
        credits=3.0,
        seat_capacity=40,
        department="CSE",
        semester=6,
    )
    in_memory_db.add_all([user, course])
    in_memory_db.commit()

    enrollment = Enrollment(
        student_id=user.id,
        course_id=course.id,
        status=EnrollmentStatus.PENDING,
        attendance=85.0,
    )
    in_memory_db.add(enrollment)
    in_memory_db.commit()
    in_memory_db.refresh(enrollment)

    assert enrollment.id is not None
    assert enrollment.status == EnrollmentStatus.PENDING
    assert enrollment.attendance == 85.0


def test_create_exam_form_model(in_memory_db: Session) -> None:
    """Test creating an ExamForm model."""
    user = User(
        email="student3@ruet.ac.bd",
        username="student3",
        full_name="Bob Brown",
        hashed_password="pw",
        role=UserRole.STUDENT,
    )
    in_memory_db.add(user)
    in_memory_db.commit()

    exam_form = ExamForm(
        student_id=user.id,
        semester=6,
        status="APPROVED",
    )
    in_memory_db.add(exam_form)
    in_memory_db.commit()
    in_memory_db.refresh(exam_form)

    assert exam_form.id is not None
    assert exam_form.student_id == user.id
    assert exam_form.status == "APPROVED"


def test_create_result_model(in_memory_db: Session) -> None:
    """Test creating a Result model."""
    user = User(
        email="student4@ruet.ac.bd",
        username="student4",
        full_name="Charlie Green",
        hashed_password="pw",
        role=UserRole.STUDENT,
    )
    course = Course(
        code="CSE 3208",
        title="Software Testing Lab",
        credits=1.5,
        seat_capacity=30,
        department="CSE",
        semester=6,
    )
    in_memory_db.add_all([user, course])
    in_memory_db.commit()

    enrollment = Enrollment(
        student_id=user.id,
        course_id=course.id,
        status=EnrollmentStatus.APPROVED,
        attendance=90.0,
    )
    in_memory_db.add(enrollment)
    in_memory_db.commit()

    result = Result(
        enrollment_id=enrollment.id,
        student_id=user.id,
        course_id=course.id,
        ca_marks=35.0,
        final_marks=52.0,
        total_marks=87.0,
        grade="A+",
        gpa=4.00,
        evaluation_status="PASS",
        is_published=False,
    )
    in_memory_db.add(result)
    in_memory_db.commit()
    in_memory_db.refresh(result)

    assert result.id is not None
    assert result.total_marks == 87.0
    assert result.grade == "A+"
    assert result.gpa == 4.00
    assert result.is_published is False


def test_create_notification_log_model(in_memory_db: Session) -> None:
    """Test creating a NotificationLog model."""
    user = User(
        email="student5@ruet.ac.bd",
        username="student5",
        full_name="Daisy White",
        hashed_password="pw",
        role=UserRole.STUDENT,
    )
    in_memory_db.add(user)
    in_memory_db.commit()

    log = NotificationLog(
        user_id=user.id,
        event_type="RESULT_PUBLISHED",
        channel="EMAIL",
        recipient="student5@ruet.ac.bd",
        message="Your result for CSE 3208 has been published.",
        status="SENT",
    )
    in_memory_db.add(log)
    in_memory_db.commit()
    in_memory_db.refresh(log)

    assert log.id is not None
    assert log.event_type == "RESULT_PUBLISHED"
    assert log.status == "SENT"


def test_database_get_db_generator() -> None:
    """Test get_db dependency yields a session and closes it."""
    gen = get_db()
    db_session = next(gen)
    assert isinstance(db_session, Session)
    # Closing generator
    with pytest.raises(StopIteration):
        next(gen)
