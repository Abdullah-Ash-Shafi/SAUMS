"""Integration tests for Result Processing, Publication, and Notification dispatch."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.models.notification import NotificationLog
from suams.models.result import Result
from suams.models.user import User


def test_publish_results_calculates_gpa_and_triggers_notifications(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Test result publication computes grades, marks published, and fires observers."""
    controller_headers = {"Authorization": f"Bearer {auth_tokens['controller']}"}
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    student = seeded_users["student"]

    # Create Course
    course = Course(code="CSE 3206", title="Software Engineering", credits=3.0, seat_capacity=50, semester=5)
    db_session.add(course)
    db_session.commit()

    # Approved Enrollment
    enrollment = Enrollment(student_id=student.id, course_id=course.id, status=EnrollmentStatus.APPROVED, attendance=85.0)
    db_session.add(enrollment)
    db_session.commit()

    # Pending Result (CA: 35, Final: 50 -> 85 Total -> A+ / 4.00)
    result = Result(
        enrollment_id=enrollment.id,
        student_id=student.id,
        course_id=course.id,
        ca_marks=35.0,
        final_marks=50.0,
        total_marks=85.0,
        evaluation_status="PASS",
        is_published=False,
    )
    db_session.add(result)
    db_session.commit()

    # Mock external email gateway to prevent external side effects
    with patch("suams.notifications.publisher.EmailDispatcher.send_email", return_value=True) as mock_email:
        response = client.post(
            "/api/results/publish",
            json={"course_id": course.id},
            headers=controller_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["course_id"] == course.id

        # Verify email dispatcher mock was called
        assert mock_email.called

    # Verify result in DB was updated with Grade, GPA, and published flag
    db_session.refresh(result)
    assert result.is_published is True
    assert result.grade == "A+"
    assert result.gpa == 4.00

    # Verify notification logs were written by observers
    logs = db_session.query(NotificationLog).filter(NotificationLog.user_id == student.id).all()
    assert len(logs) >= 2  # InApp and Email observers
    channels = [log.channel for log in logs]
    assert "IN_APP" in channels
    assert "EMAIL" in channels


def test_student_can_view_published_results(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Student can retrieve their own published academic results."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    student = seeded_users["student"]

    course = Course(code="CSE 3208", title="Testing Lab", credits=1.5, seat_capacity=50, semester=5)
    db_session.add(course)
    db_session.commit()

    enrollment = Enrollment(student_id=student.id, course_id=course.id, status=EnrollmentStatus.APPROVED, attendance=90.0)
    db_session.add(enrollment)
    db_session.commit()

    # Published result
    result = Result(
        enrollment_id=enrollment.id,
        student_id=student.id,
        course_id=course.id,
        ca_marks=38.0,
        final_marks=56.0,
        total_marks=94.0,
        grade="A+",
        gpa=4.00,
        evaluation_status="PASS",
        is_published=True,
    )
    db_session.add(result)
    db_session.commit()

    response = client.get("/api/results/my-results", headers=student_headers)
    assert response.status_code == 200
    my_results = response.json()
    assert len(my_results) >= 1
    res_entry = my_results[0]
    assert res_entry["grade"] == "A+"
    assert res_entry["gpa"] == 4.00


def test_advising_approval_triggers_observer_notification(
    client: TestClient,
    auth_tokens: dict[str, str],
    seeded_users: dict[str, User],
    db_session: Session,
) -> None:
    """Approving course registration triggers academic event and notification dispatch."""
    student = seeded_users["student"]
    teacher_headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}

    course = Course(code="CSE 3216", title="Distributed Systems", credits=3.0, seat_capacity=40, semester=5)
    db_session.add(course)
    db_session.commit()

    enrollment = Enrollment(student_id=student.id, course_id=course.id, status=EnrollmentStatus.PENDING, attendance=0.0)
    db_session.add(enrollment)
    db_session.commit()

    with patch("suams.notifications.publisher.EmailDispatcher.send_email", return_value=True):
        response = client.put(
            f"/api/registration/advisor/approve/{enrollment.id}",
            headers=teacher_headers,
        )
        assert response.status_code == 200

    # Verify notification log created for REGISTRATION_APPROVED
    logs = (
        db_session.query(NotificationLog)
        .filter(
            NotificationLog.user_id == student.id,
            NotificationLog.event_type == "REGISTRATION_APPROVED",
        )
        .all()
    )
    assert len(logs) >= 1
