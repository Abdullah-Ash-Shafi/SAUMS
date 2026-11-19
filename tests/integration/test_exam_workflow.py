"""Integration tests for Exam Form Generation and Evaluation workflow."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.models.user import User


def test_exam_form_contains_only_approved_courses(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Test that exam form generation strictly includes only APPROVED courses."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    student = seeded_users["student"]

    # Create 3 courses
    c1 = Course(code="CSE 3201", title="Operating Systems", credits=3.0, seat_capacity=50, semester=5)
    c2 = Course(code="CSE 3203", title="Computer Networks", credits=3.0, seat_capacity=50, semester=5)
    c3 = Course(code="CSE 3205", title="Microprocessors", credits=3.0, seat_capacity=50, semester=5)
    db_session.add_all([c1, c2, c3])
    db_session.commit()

    # Enrollments: c1 APPROVED, c2 PENDING, c3 REJECTED
    e1 = Enrollment(student_id=student.id, course_id=c1.id, status=EnrollmentStatus.APPROVED, attendance=85.0)
    e2 = Enrollment(student_id=student.id, course_id=c2.id, status=EnrollmentStatus.PENDING, attendance=80.0)
    e3 = Enrollment(student_id=student.id, course_id=c3.id, status=EnrollmentStatus.REJECTED, attendance=90.0)
    db_session.add_all([e1, e2, e3])
    db_session.commit()

    # Student requests exam form generation for semester 5
    response = client.post(
        "/api/exams/form/generate",
        json={"semester": 5},
        headers=student_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == student.id
    assert data["semester"] == 5
    assert data["status"] == "APPROVED"

    # Crucial check: ONLY c1 must be present in approved_courses
    course_codes = [c["code"] for c in data["approved_courses"]]
    assert "CSE 3201" in course_codes
    assert "CSE 3203" not in course_codes
    assert "CSE 3205" not in course_codes


def test_exam_form_generation_fails_if_no_approved_courses(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Test that exam form generation returns 400 Bad Request if no approved courses exist."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    student = seeded_users["student"]

    c = Course(code="CSE 3209", title="Compiler Design", credits=3.0, seat_capacity=50, semester=5)
    db_session.add(c)
    db_session.commit()

    e = Enrollment(student_id=student.id, course_id=c.id, status=EnrollmentStatus.PENDING, attendance=80.0)
    db_session.add(e)
    db_session.commit()

    response = client.post(
        "/api/exams/form/generate",
        json={"semester": 5},
        headers=student_headers,
    )
    assert response.status_code == 400
    assert "No approved course enrollments found" in response.json()["detail"]


def test_teacher_mark_entry_pass_path(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Teacher enters marks (CA: 30, Final: 45 -> 75 Total) with attendance >= 75% -> PASS."""
    teacher_headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    student = seeded_users["student"]

    c = Course(code="CSE 3211", title="Algorithm Engineering", credits=3.0, seat_capacity=50, semester=5)
    db_session.add(c)
    db_session.commit()

    e = Enrollment(student_id=student.id, course_id=c.id, status=EnrollmentStatus.APPROVED, attendance=80.0)
    db_session.add(e)
    db_session.commit()

    response = client.post(
        "/api/exams/marks/entry",
        json={
            "student_id": student.id,
            "course_id": c.id,
            "ca_marks": 30.0,
            "final_marks": 45.0,
        },
        headers=teacher_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_marks"] == 75.0
    assert data["evaluation_status"] == "PASS"


def test_teacher_mark_entry_fail_path(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Teacher enters marks (CA: 15, Final: 20 -> 35 Total) with attendance >= 75% -> FAIL."""
    teacher_headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    student = seeded_users["student"]

    c = Course(code="CSE 3213", title="Simulation", credits=3.0, seat_capacity=50, semester=5)
    db_session.add(c)
    db_session.commit()

    e = Enrollment(student_id=student.id, course_id=c.id, status=EnrollmentStatus.APPROVED, attendance=82.0)
    db_session.add(e)
    db_session.commit()

    response = client.post(
        "/api/exams/marks/entry",
        json={
            "student_id": student.id,
            "course_id": c.id,
            "ca_marks": 15.0,
            "final_marks": 20.0,
        },
        headers=teacher_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_marks"] == 35.0
    assert data["evaluation_status"] == "FAIL"


def test_teacher_mark_entry_disqualified_path(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Teacher enters marks for student with attendance < 75% -> DISQUALIFIED."""
    teacher_headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    student = seeded_users["student"]

    c = Course(code="CSE 3215", title="VLSI Design", credits=3.0, seat_capacity=50, semester=5)
    db_session.add(c)
    db_session.commit()

    # Attendance 65% (< 75%)
    e = Enrollment(student_id=student.id, course_id=c.id, status=EnrollmentStatus.APPROVED, attendance=65.0)
    db_session.add(e)
    db_session.commit()

    response = client.post(
        "/api/exams/marks/entry",
        json={
            "student_id": student.id,
            "course_id": c.id,
            "ca_marks": 35.0,
            "final_marks": 50.0,
        },
        headers=teacher_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation_status"] == "DISQUALIFIED"


def test_student_cannot_submit_marks(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
) -> None:
    """Student attempting teacher mark entry must return HTTP 403 Forbidden."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    response = client.post(
        "/api/exams/marks/entry",
        json={
            "student_id": 1,
            "course_id": 1,
            "ca_marks": 30.0,
            "final_marks": 50.0,
        },
        headers=student_headers,
    )
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]
