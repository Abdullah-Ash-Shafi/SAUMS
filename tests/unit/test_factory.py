"""Unit tests for UserDashboardFactory (Factory Pattern)."""
from unittest.mock import MagicMock
import pytest

from suams.models.user import UserRole
from suams.users.factory import (
    UserDashboardFactory,
    StudentDashboard,
    TeacherDashboard,
    AdminDashboard,
    ControllerDashboard,
)


def test_factory_creates_student_dashboard() -> None:
    """Test UserDashboardFactory creates StudentDashboard for STUDENT role."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "student@ruet.ac.bd"
    mock_user.username = "student_user"
    mock_user.full_name = "Student Name"
    mock_user.role = UserRole.STUDENT
    mock_user.department = "CSE"
    mock_user.semester = 5

    dashboard = UserDashboardFactory.create_dashboard(mock_user)

    assert isinstance(dashboard, StudentDashboard)
    assert dashboard.user_id == 1
    assert dashboard.role == UserRole.STUDENT
    assert dashboard.semester == 5
    assert "Course Registration" in dashboard.menu_items
    assert "Exam Form" in dashboard.menu_items


def test_factory_creates_teacher_dashboard() -> None:
    """Test UserDashboardFactory creates TeacherDashboard for TEACHER role."""
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.email = "teacher@ruet.ac.bd"
    mock_user.username = "teacher_user"
    mock_user.full_name = "Teacher Name"
    mock_user.role = UserRole.TEACHER
    mock_user.department = "CSE"
    mock_user.semester = None

    dashboard = UserDashboardFactory.create_dashboard(mock_user)

    assert isinstance(dashboard, TeacherDashboard)
    assert dashboard.user_id == 2
    assert dashboard.role == UserRole.TEACHER
    assert "Evaluation" in dashboard.menu_items or "Mark Entry" in dashboard.menu_items


def test_factory_creates_admin_dashboard() -> None:
    """Test UserDashboardFactory creates AdminDashboard for DEPARTMENT_ADMIN role."""
    mock_user = MagicMock()
    mock_user.id = 3
    mock_user.email = "admin@ruet.ac.bd"
    mock_user.username = "admin_user"
    mock_user.full_name = "Admin Name"
    mock_user.role = UserRole.DEPARTMENT_ADMIN
    mock_user.department = "CSE"
    mock_user.semester = None

    dashboard = UserDashboardFactory.create_dashboard(mock_user)

    assert isinstance(dashboard, AdminDashboard)
    assert dashboard.user_id == 3
    assert dashboard.role == UserRole.DEPARTMENT_ADMIN
    assert "Course Catalog" in dashboard.menu_items


def test_factory_creates_controller_dashboard() -> None:
    """Test UserDashboardFactory creates ControllerDashboard for EXAM_CONTROLLER role."""
    mock_user = MagicMock()
    mock_user.id = 4
    mock_user.email = "controller@ruet.ac.bd"
    mock_user.username = "controller_user"
    mock_user.full_name = "Controller Name"
    mock_user.role = UserRole.EXAM_CONTROLLER
    mock_user.department = "ControllerOffice"
    mock_user.semester = None

    dashboard = UserDashboardFactory.create_dashboard(mock_user)

    assert isinstance(dashboard, ControllerDashboard)
    assert dashboard.user_id == 4
    assert dashboard.role == UserRole.EXAM_CONTROLLER
    assert "Publish Results" in dashboard.menu_items


def test_factory_invalid_role_raises_value_error() -> None:
    """Test UserDashboardFactory raises ValueError when unknown role is passed."""
    mock_user = MagicMock()
    mock_user.role = "SuperUserNonExistent"

    with pytest.raises(ValueError) as exc_info:
        UserDashboardFactory.create_dashboard(mock_user)

    assert "Unsupported role" in str(exc_info.value)
