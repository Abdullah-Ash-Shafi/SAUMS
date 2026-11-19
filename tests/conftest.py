"""Pytest configuration and shared fixtures."""
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from suams.database import Base, get_db
from suams.main import app
from suams.models.user import User, UserRole
from suams.auth.security import get_password_hash, create_access_token


@pytest.fixture(scope="session")
def engine():
    """Create in-memory SQLite engine with StaticPool for thread sharing."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_users(db_session: Session) -> dict[str, User]:
    """Seed test users for each role."""
    users = {
        "student": User(
            email="student@ruet.ac.bd",
            username="student_user",
            full_name="Student User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.STUDENT,
            department="CSE",
            semester=5,
            is_active=True,
        ),
        "teacher": User(
            email="teacher@ruet.ac.bd",
            username="teacher_user",
            full_name="Teacher User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.TEACHER,
            department="CSE",
            semester=None,
            is_active=True,
        ),
        "admin": User(
            email="admin@ruet.ac.bd",
            username="admin_user",
            full_name="Admin User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.DEPARTMENT_ADMIN,
            department="CSE",
            semester=None,
            is_active=True,
        ),
        "controller": User(
            email="controller@ruet.ac.bd",
            username="controller_user",
            full_name="Exam Controller",
            hashed_password=get_password_hash("password123"),
            role=UserRole.EXAM_CONTROLLER,
            department="ExamControllerOffice",
            semester=None,
            is_active=True,
        ),
    }
    for user in users.values():
        db_session.add(user)
    db_session.commit()
    for user in users.values():
        db_session.refresh(user)
    return users


@pytest.fixture
def auth_tokens(seeded_users: dict[str, User]) -> dict[str, str]:
    """Generate auth tokens for seeded users."""
    tokens = {}
    for role_key, user in seeded_users.items():
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        tokens[role_key] = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": role_val}
        )
    return tokens
