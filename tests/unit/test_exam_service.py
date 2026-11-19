"""Unit tests for Exam Service and White-Box Basis-Path Testing (TDD First).

Basis-Path Testing for evaluateResult(is_enrolled, attendance, total_marks):
Cyclomatic Complexity V(G) = Predicate Nodes (3) + 1 = 4 Independent Paths.

Path 1 (TC-WB-01): Not enrolled -> "NOT_ENROLLED"
Path 2 (TC-WB-02): Enrolled, attendance < 75 -> "DISQUALIFIED"
Path 3 (TC-WB-03): Enrolled, attendance >= 75, total_marks >= 40 -> "PASS"
Path 4 (TC-WB-04): Enrolled, attendance >= 75, total_marks < 40 -> "FAIL"
"""
from unittest.mock import MagicMock
import pytest

from suams.exams.service import (
    evaluateResult,
    ExamService,
)
from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.models.exam import ExamForm


# ============================================================================
# Basis-Path Testing (TC-WB-01 to TC-WB-04)
# ============================================================================


def test_tc_wb_01_basis_path_1_not_enrolled() -> None:
    """TC-WB-01: Path 1 -> is_enrolled is False.

    Regardless of attendance and total_marks, result must be 'NOT_ENROLLED'.
    """
    result = evaluateResult(is_enrolled=False, attendance=85.0, total_marks=75.0)
    assert result == "NOT_ENROLLED"


def test_tc_wb_02_basis_path_2_attendance_disqualified() -> None:
    """TC-WB-02: Path 2 -> is_enrolled is True, attendance < 75.0.

    Even if total_marks >= 40, insufficient attendance results in 'DISQUALIFIED'.
    """
    result = evaluateResult(is_enrolled=True, attendance=74.9, total_marks=80.0)
    assert result == "DISQUALIFIED"


def test_tc_wb_03_basis_path_3_pass() -> None:
    """TC-WB-03: Path 3 -> is_enrolled is True, attendance >= 75.0, total_marks >= 40.0.

    Satisfies attendance and minimum passing marks -> 'PASS'.
    """
    result = evaluateResult(is_enrolled=True, attendance=75.0, total_marks=40.0)
    assert result == "PASS"


def test_tc_wb_04_basis_path_4_fail() -> None:
    """TC-WB-04: Path 4 -> is_enrolled is True, attendance >= 75.0, total_marks < 40.0.

    Satisfies attendance but total_marks < 40 -> 'FAIL'.
    """
    result = evaluateResult(is_enrolled=True, attendance=90.0, total_marks=39.9)
    assert result == "FAIL"


# ============================================================================
# Exam Form Generation Tests (Only APPROVED courses appear)
# ============================================================================


def test_generate_exam_form_only_approved_courses_mocked() -> None:
    """Test that exam form generation strictly filters for APPROVED enrollments."""
    mock_db = MagicMock()
    student_id = 7
    semester = 6

    # 3 mock enrollments: 1 APPROVED, 1 PENDING, 1 REJECTED
    c1 = MagicMock(spec=Course, id=1, code="CSE 3206", title="Software Engineering", credits=3.0)
    c2 = MagicMock(spec=Course, id=2, code="CSE 3208", title="Testing Lab", credits=1.5)
    c3 = MagicMock(spec=Course, id=3, code="CSE 3210", title="Network Lab", credits=1.5)

    e1 = MagicMock(spec=Enrollment, id=10, student_id=student_id, course_id=1, status=EnrollmentStatus.APPROVED, course=c1)
    e2 = MagicMock(spec=Enrollment, id=11, student_id=student_id, course_id=2, status=EnrollmentStatus.PENDING, course=c2)
    e3 = MagicMock(spec=Enrollment, id=12, student_id=student_id, course_id=3, status=EnrollmentStatus.REJECTED, course=c3)

    # Mock DB query for student enrollments
    mock_db.query.return_value.filter.return_value.all.return_value = [e1, e2, e3]

    exam_form, courses = ExamService.generate_exam_form(student_id=student_id, semester=semester, db=mock_db)

    # Verification: Only course 1 (e1, APPROVED) must be present in the exam form
    assert len(courses) == 1
    assert courses[0].code == "CSE 3206"
    assert exam_form.student_id == student_id
    assert exam_form.status == "APPROVED"
    mock_db.commit.assert_called_once()


def test_generate_exam_form_no_approved_courses_raises_error() -> None:
    """Test generating exam form with zero approved courses raises ValueError."""
    mock_db = MagicMock()
    student_id = 8
    semester = 6

    # Only pending enrollment
    e_pending = MagicMock(spec=Enrollment, status=EnrollmentStatus.PENDING)
    mock_db.query.return_value.filter.return_value.all.return_value = [e_pending]

    with pytest.raises(ValueError) as exc:
        ExamService.generate_exam_form(student_id=student_id, semester=semester, db=mock_db)

    assert "No approved course enrollments found" in str(exc.value)


# ============================================================================
# Teacher Mark Entry Validation Tests
# ============================================================================


def test_mark_entry_validations() -> None:
    """Test validation boundaries for Continuous Assessment (0-40) and Final Exam (0-60)."""
    mock_db = MagicMock()

    # Invalid CA marks (> 40)
    with pytest.raises(ValueError) as exc1:
        ExamService.submit_marks(
            student_id=1, course_id=1, ca_marks=40.5, final_marks=50.0, db=mock_db
        )
    assert "Continuous Assessment (CA) marks must be between 0 and 40" in str(exc1.value)

    # Invalid CA marks (< 0)
    with pytest.raises(ValueError) as exc2:
        ExamService.submit_marks(
            student_id=1, course_id=1, ca_marks=-1.0, final_marks=50.0, db=mock_db
        )
    assert "Continuous Assessment (CA) marks must be between 0 and 40" in str(exc2.value)

    # Invalid Final marks (> 60)
    with pytest.raises(ValueError) as exc3:
        ExamService.submit_marks(
            student_id=1, course_id=1, ca_marks=35.0, final_marks=60.5, db=mock_db
        )
    assert "Final Exam marks must be between 0 and 60" in str(exc3.value)

    # Invalid Final marks (< 0)
    with pytest.raises(ValueError) as exc4:
        ExamService.submit_marks(
            student_id=1, course_id=1, ca_marks=35.0, final_marks=-2.0, db=mock_db
        )
    assert "Final Exam marks must be between 0 and 60" in str(exc4.value)
