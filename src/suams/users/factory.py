"""Creational Design Pattern: Factory Pattern for User Dashboards.

This module implements the Factory Pattern (Creational) to decouple the creation
of role-specific dashboard and profile payloads from client code.
Depending on the user's role (Student, Teacher, DepartmentAdmin, ExamController),
the `UserDashboardFactory` instantiates and returns the corresponding concrete
dashboard payload (`StudentDashboard`, `TeacherDashboard`, `AdminDashboard`,
or `ControllerDashboard`).
"""
from dataclasses import dataclass, field
from typing import Any, Optional
from suams.models.user import User, UserRole


@dataclass
class BaseDashboardPayload:
    """Abstract base class / data structure for user dashboard payloads."""

    user_id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str]
    menu_items: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentDashboard(BaseDashboardPayload):
    """Concrete dashboard payload for Students.

    Includes semester progress, registered courses, exam eligibility,
    and student-specific navigation.
    """

    semester: Optional[int] = None
    enrolled_courses: list[dict[str, Any]] = field(default_factory=list)
    cgpa: Optional[float] = None
    exam_form_status: Optional[str] = None


@dataclass
class TeacherDashboard(BaseDashboardPayload):
    """Concrete dashboard payload for Faculty / Teachers.

    Includes assigned courses, pending evaluations for Continuous Assessment (CA)
    and final marks entry.
    """

    assigned_courses: list[dict[str, Any]] = field(default_factory=list)
    pending_evaluations_count: int = 0


@dataclass
class AdminDashboard(BaseDashboardPayload):
    """Concrete dashboard payload for Department Administrators.

    Includes department course catalog management, advising workflow oversight,
    and student onboarding statistics.
    """

    total_students: int = 0
    total_courses: int = 0
    pending_advising_count: int = 0


@dataclass
class ControllerDashboard(BaseDashboardPayload):
    """Concrete dashboard payload for Exam Controllers.

    Includes grade approval queues, result publication controls,
    and academic notification dispatch summaries.
    """

    published_results_count: int = 0
    pending_publication_count: int = 0
    grading_system: str = "Standard RUET Grading System"


class UserDashboardFactory:
    """Factory class responsible for creating role-specific dashboard payloads.

    This implements the Factory Method creational pattern. Clients do not need
    to know the specific concrete class being instantiated, only that they
    receive an appropriate role-specialized dashboard payload.
    """

    @staticmethod
    def create_dashboard(user: User, **kwargs: Any) -> BaseDashboardPayload:
        """Instantiate and return the appropriate dashboard payload based on user role.

        Args:
            user: The User instance or duck-typed user object.
            **kwargs: Optional additional context data to enrich the dashboard.

        Returns:
            An instance of StudentDashboard, TeacherDashboard, AdminDashboard,
            or ControllerDashboard.

        Raises:
            ValueError: If the user's role is not recognized or supported.
        """
        role = user.role
        user_id = user.id
        username = user.username
        email = user.email
        full_name = getattr(user, "full_name", username)
        department = getattr(user, "department", None)

        if role == UserRole.STUDENT or role == "Student":
            return StudentDashboard(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                role=UserRole.STUDENT,
                department=department,
                semester=getattr(user, "semester", None),
                menu_items=[
                    "My Courses",
                    "Course Registration",
                    "Exam Form",
                    "Results & Transcript",
                ],
                enrolled_courses=kwargs.get("enrolled_courses", []),
                cgpa=kwargs.get("cgpa", None),
                exam_form_status=kwargs.get("exam_form_status", None),
            )

        if role == UserRole.TEACHER or role == "Teacher":
            return TeacherDashboard(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                role=UserRole.TEACHER,
                department=department,
                menu_items=[
                    "My Assigned Courses",
                    "Continuous Assessment (CA)",
                    "Mark Entry",
                    "Evaluation",
                ],
                assigned_courses=kwargs.get("assigned_courses", []),
                pending_evaluations_count=kwargs.get("pending_evaluations_count", 0),
            )

        if role == UserRole.DEPARTMENT_ADMIN or role == "DepartmentAdmin":
            return AdminDashboard(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                role=UserRole.DEPARTMENT_ADMIN,
                department=department,
                menu_items=[
                    "Department Overview",
                    "Course Catalog",
                    "Student Admissions",
                    "Advising Approvals",
                ],
                total_students=kwargs.get("total_students", 0),
                total_courses=kwargs.get("total_courses", 0),
                pending_advising_count=kwargs.get("pending_advising_count", 0),
            )

        if role == UserRole.EXAM_CONTROLLER or role == "ExamController":
            return ControllerDashboard(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                role=UserRole.EXAM_CONTROLLER,
                department=department,
                menu_items=[
                    "Exam Clearance",
                    "Grade Approval",
                    "Publish Results",
                    "Notification Dispatch Logs",
                ],
                published_results_count=kwargs.get("published_results_count", 0),
                pending_publication_count=kwargs.get("pending_publication_count", 0),
            )

        raise ValueError(f"Unsupported role '{role}' for dashboard generation.")
