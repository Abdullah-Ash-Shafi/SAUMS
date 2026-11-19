"""Integration tests for Authentication and RBAC."""
from fastapi.testclient import TestClient
from suams.models.user import User


def test_login_success(client: TestClient, seeded_users: dict[str, User]) -> None:
    """Test login with valid credentials returns access token."""
    response = client.post(
        "/api/auth/login",
        json={"username": "student_user", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "Student"


def test_login_invalid_password(client: TestClient, seeded_users: dict[str, User]) -> None:
    """Test login with incorrect password returns 401."""
    response = client.post(
        "/api/auth/login",
        json={"username": "student_user", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient, seeded_users: dict[str, User]) -> None:
    """Test login with non-existent username returns 401."""
    response = client.post(
        "/api/auth/login",
        json={"username": "unknown_user", "password": "password123"},
    )
    assert response.status_code == 401


def test_unauthenticated_access_returns_401(client: TestClient) -> None:
    """Accessing protected endpoints without token must return 401."""
    response = client.get("/api/users/dashboard")
    assert response.status_code == 401


def test_student_cannot_access_teacher_restricted_endpoint(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """Student accessing teacher-only endpoint must return HTTP 403 Forbidden."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    response = client.get("/api/exams/teacher/evaluation-queue", headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


def test_student_cannot_access_results_publish_endpoint(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """Student accessing ExamController restricted /api/results/publish must return HTTP 403 Forbidden."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    response = client.post("/api/results/publish", json={"course_id": 1}, headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


def test_teacher_cannot_access_results_publish_endpoint(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """Teacher accessing ExamController restricted /api/results/publish must return HTTP 403 Forbidden."""
    headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    response = client.post("/api/results/publish", json={"course_id": 1}, headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


def test_teacher_can_access_teacher_endpoint(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """Teacher token grants access to teacher endpoints."""
    headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    response = client.get("/api/exams/teacher/evaluation-queue", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_controller_can_access_results_publish_endpoint(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """ExamController token grants access to /api/results/publish."""
    headers = {"Authorization": f"Bearer {auth_tokens['controller']}"}
    response = client.post("/api/results/publish", json={"course_id": 1}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_user_dashboard_endpoint_returns_student_payload(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """Student accessing /api/users/dashboard gets StudentDashboard payload."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}
    response = client.get("/api/users/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Student"
    assert "Course Registration" in data["menu_items"]


def test_user_dashboard_endpoint_returns_teacher_payload(
    client: TestClient, auth_tokens: dict[str, str]
) -> None:
    """Teacher accessing /api/users/dashboard gets TeacherDashboard payload."""
    headers = {"Authorization": f"Bearer {auth_tokens['teacher']}"}
    response = client.get("/api/users/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Teacher"
