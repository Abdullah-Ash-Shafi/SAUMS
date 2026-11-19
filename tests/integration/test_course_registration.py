"""Integration tests for Course Registration and Advising workflow."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from suams.models.course import Course
from suams.models.user import User


@pytest.fixture
def sample_courses(db_session: Session) -> dict[str, Course]:
    """Seed test courses with prerequisites and capacities."""
    c1 = Course(
        code="CSE 1101",
        title="Structured Programming",
        credits=3.0,
        seat_capacity=2,  # small capacity to test full course
        department="CSE",
        semester=1,
    )
    db_session.add(c1)
    db_session.commit()
    db_session.refresh(c1)

    c2 = Course(
        code="CSE 2101",
        title="Object Oriented Programming",
        credits=3.0,
        seat_capacity=50,
        department="CSE",
        semester=3,
        prerequisite_id=c1.id,  # requires CSE 1101
    )
    c3 = Course(
        code="CSE 3206",
        title="Software Engineering",
        credits=3.0,
        seat_capacity=50,
        department="CSE",
        semester=6,
    )
    c4 = Course(
        code="CSE 3200",
        title="High Credit Project",
        credits=22.0,
        seat_capacity=10,
        department="CSE",
        semester=6,
    )
    db_session.add_all([c2, c3, c4])
    db_session.commit()
    for c in [c2, c3, c4]:
        db_session.refresh(c)

    return {"c1": c1, "c2": c2, "c3": c3, "c4": c4}


def test_student_can_view_courses(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Student can view the course catalog."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    response = client.get("/api/registration/courses", headers=headers)
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) >= 4
    course_codes = [c["code"] for c in courses]
    assert "CSE 1101" in course_codes


def test_student_course_registration_success(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Student can register for an available course without prerequisites."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    course = sample_courses["c1"]

    response = client.post(
        "/api/registration/register",
        json={"course_id": course.id},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["course_id"] == course.id


def test_student_cannot_register_duplicate_course(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Registering for the same course twice returns 400 Bad Request."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    course = sample_courses["c3"]

    r1 = client.post("/api/registration/register", json={"course_id": course.id}, headers=headers)
    assert r1.status_code == 200

    r2 = client.post("/api/registration/register", json={"course_id": course.id}, headers=headers)
    assert r2.status_code == 400
    assert "Already registered" in r2.json()["detail"]


def test_student_cannot_register_if_prerequisite_not_met(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Registering for a course whose prerequisite is not completed returns 400 Bad Request."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    dependent_course = sample_courses["c2"]  # requires c1

    response = client.post(
        "/api/registration/register",
        json={"course_id": dependent_course.id},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Prerequisite" in response.json()["detail"]


def test_student_cannot_register_when_seat_capacity_full(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
    db_session: Session,
    seeded_users: dict[str, User],
) -> None:
    """Registering when course capacity is reached returns 400 Bad Request."""
    headers_student = {"Authorization": f"Bearer {auth_tokens['student']}"}
    course = sample_courses["c1"]  # seat_capacity is 2

    # Register first student
    r1 = client.post("/api/registration/register", json={"course_id": course.id}, headers=headers_student)
    assert r1.status_code == 200

    # Create and login another student to fill the second seat
    from suams.models.user import UserRole
    from suams.auth.security import get_password_hash
    other_student = User(
        email="other@ruet.ac.bd",
        username="other_student",
        full_name="Other Student",
        hashed_password=get_password_hash("pw"),
        role=UserRole.STUDENT,
    )
    db_session.add(other_student)
    db_session.commit()
    db_session.refresh(other_student)

    from suams.auth.security import create_access_token
    token_other = create_access_token(data={"sub": other_student.username, "user_id": other_student.id, "role": "Student"})
    headers_other = {"Authorization": f"Bearer {token_other}"}

    r2 = client.post("/api/registration/register", json={"course_id": course.id}, headers=headers_other)
    assert r2.status_code == 200

    # Create third student who tries to register for full course
    third_student = User(
        email="third@ruet.ac.bd",
        username="third_student",
        full_name="Third Student",
        hashed_password=get_password_hash("pw"),
        role=UserRole.STUDENT,
    )
    db_session.add(third_student)
    db_session.commit()
    db_session.refresh(third_student)

    token_third = create_access_token(data={"sub": third_student.username, "user_id": third_student.id, "role": "Student"})
    headers_third = {"Authorization": f"Bearer {token_third}"}

    r3 = client.post("/api/registration/register", json={"course_id": course.id}, headers=headers_third)
    assert r3.status_code == 400
    assert "capacity" in r3.json()["detail"].lower()


def test_advisor_approval_workflow(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Test advisor approving and rejecting course registrations."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    teacher_headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    course = sample_courses["c3"]

    # Student registers
    r_reg = client.post("/api/registration/register", json={"course_id": course.id}, headers=student_headers)
    assert r_reg.status_code == 200
    enrollment_id = r_reg.json()["id"]
    assert r_reg.json()["status"] == "PENDING"

    # Student tries to approve own registration -> 403 Forbidden
    r_forbidden = client.put(f"/api/registration/advisor/approve/{enrollment_id}", headers=student_headers)
    assert r_forbidden.status_code == 403

    # Advisor views pending queue
    r_pending = client.get("/api/registration/advisor/pending", headers=teacher_headers)
    assert r_pending.status_code == 200
    pending_ids = [e["id"] for e in r_pending.json()]
    assert enrollment_id in pending_ids

    # Advisor approves registration
    r_approve = client.put(f"/api/registration/advisor/approve/{enrollment_id}", headers=teacher_headers)
    assert r_approve.status_code == 200
    assert r_approve.json()["status"] == "APPROVED"


def test_advisor_reject_workflow(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Test advisor rejecting a course registration."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    teacher_headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    course = sample_courses["c3"]

    r_reg = client.post("/api/registration/register", json={"course_id": course.id}, headers=student_headers)
    enrollment_id = r_reg.json()["id"]

    # Advisor rejects registration
    r_reject = client.put(f"/api/registration/advisor/reject/{enrollment_id}", headers=teacher_headers)
    assert r_reject.status_code == 200
    assert r_reject.json()["status"] == "REJECTED"


def test_student_view_my_courses(
    client: TestClient,
    auth_tokens: dict[str, str],
    sample_courses: dict[str, Course],
) -> None:
    """Student can view their enrolled and registered courses."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    course = sample_courses["c1"]

    client.post("/api/registration/register", json={"course_id": course.id}, headers=student_headers)

    response = client.get("/api/registration/my-courses", headers=student_headers)
    assert response.status_code == 200
    enrolled = response.json()
    assert len(enrolled) >= 1
    assert enrolled[0]["course_id"] == course.id
