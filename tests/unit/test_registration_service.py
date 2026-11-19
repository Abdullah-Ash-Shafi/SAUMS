"""Unit tests for Course Registration and Advising Service (TDD First).

Tests Boundary-Value Analysis (BVA) for checkCreditLimit (11, 12, 24, 25 credits),
seat capacity checks, prerequisite verification, and advisor workflow transitions.
Uses unittest.mock (MagicMock) to isolate external database dependencies.
"""
from unittest.mock import MagicMock
import pytest

from suams.models.course import Course
from suams.models.enrollment import Enrollment, EnrollmentStatus
from suams.registration.service import (
    checkCreditLimit,
    check_seat_capacity,
    check_prerequisites,
    RegistrationService,
)


# ============================================================================
# Boundary-Value Analysis (BVA) for checkCreditLimit
# Boundaries: Minimum = 12 credits, Maximum = 24 credits (inclusive)
# Values tested: 11 (invalid, <12), 12 (valid, min), 24 (valid, max), 25 (invalid, >24)
# ============================================================================


def test_check_credit_limit_boundary_11_invalid() -> None:
    """BVA Test: 11 credits is below minimum limit of 12 credits -> False."""
    assert checkCreditLimit(student_id=1, new_course_credits=11.0, current_credits=0.0) is False


def test_check_credit_limit_boundary_12_valid() -> None:
    """BVA Test: 12 credits is the exact minimum valid semester load -> True."""
    assert checkCreditLimit(student_id=1, new_course_credits=12.0, current_credits=0.0) is True


def test_check_credit_limit_boundary_24_valid() -> None:
    """BVA Test: 24 credits is the exact maximum valid semester load -> True."""
    assert checkCreditLimit(student_id=1, new_course_credits=24.0, current_credits=0.0) is True


def test_check_credit_limit_boundary_25_invalid() -> None:
    """BVA Test: 25 credits exceeds maximum limit of 24 credits -> False."""
    assert checkCreditLimit(student_id=1, new_course_credits=25.0, current_credits=0.0) is False


def test_check_credit_limit_with_mocked_db_session() -> None:
    """Test checkCreditLimit calculating load from mocked database session."""
    mock_db = MagicMock()
    student_id = 42

    # Case 1: Student has 9 credits, wants to add 2 credits -> 11 credits (Invalid)
    course_mock_1 = MagicMock(spec=Course)
    course_mock_1.credits = 9.0
    enrollment_mock_1 = MagicMock(spec=Enrollment)
    enrollment_mock_1.course = course_mock_1
    enrollment_mock_1.status = EnrollmentStatus.APPROVED

    mock_db.query.return_value.filter.return_value.all.return_value = [enrollment_mock_1]
    assert checkCreditLimit(student_id=student_id, new_course_credits=2.0, db=mock_db) is False

    # Case 2: Student has 9 credits, wants to add 3 credits -> 12 credits (Valid minimum)
    assert checkCreditLimit(student_id=student_id, new_course_credits=3.0, db=mock_db) is True

    # Case 3: Student has 20 credits, wants to add 4 credits -> 24 credits (Valid maximum)
    course_mock_2 = MagicMock(spec=Course)
    course_mock_2.credits = 20.0
    enrollment_mock_2 = MagicMock(spec=Enrollment)
    enrollment_mock_2.course = course_mock_2
    enrollment_mock_2.status = EnrollmentStatus.APPROVED

    mock_db.query.return_value.filter.return_value.all.return_value = [enrollment_mock_2]
    assert checkCreditLimit(student_id=student_id, new_course_credits=4.0, db=mock_db) is True

    # Case 4: Student has 20 credits, wants to add 5 credits -> 25 credits (Invalid)
    assert checkCreditLimit(student_id=student_id, new_course_credits=5.0, db=mock_db) is False


# ============================================================================
# Seat Capacity Verification Tests
# ============================================================================


def test_check_seat_capacity_available() -> None:
    """Test seat capacity check when open seats exist."""
    mock_db = MagicMock()
    mock_course = MagicMock(spec=Course)
    mock_course.id = 101
    mock_course.seat_capacity = 60
    mock_db.query.return_value.filter.return_value.first.return_value = mock_course

    # 40 enrolled students
    mock_db.query.return_value.filter.return_value.count.return_value = 40

    assert check_seat_capacity(course_id=101, db=mock_db) is True


def test_check_seat_capacity_full() -> None:
    """Test seat capacity check when course is fully booked."""
    mock_db = MagicMock()
    mock_course = MagicMock(spec=Course)
    mock_course.id = 101
    mock_course.seat_capacity = 60
    mock_db.query.return_value.filter.return_value.first.return_value = mock_course

    # 60 enrolled students (full)
    mock_db.query.return_value.filter.return_value.count.return_value = 60

    assert check_seat_capacity(course_id=101, db=mock_db) is False


def test_check_seat_capacity_nonexistent_course() -> None:
    """Test seat capacity check raises ValueError for nonexistent course."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError) as exc:
        check_seat_capacity(course_id=999, db=mock_db)
    assert "Course not found" in str(exc.value)


# ============================================================================
# Prerequisites Verification Tests
# ============================================================================


def test_check_prerequisites_no_prerequisite_required() -> None:
    """Course with no prerequisite returns True."""
    mock_db = MagicMock()
    mock_course = MagicMock(spec=Course)
    mock_course.id = 10
    mock_course.prerequisite_id = None
    mock_db.query.return_value.filter.return_value.first.return_value = mock_course

    assert check_prerequisites(student_id=1, course_id=10, db=mock_db) is True


def test_check_prerequisites_prerequisite_satisfied() -> None:
    """Course with prerequisite satisfied by approved enrollment returns True."""
    mock_db = MagicMock()
    mock_course = MagicMock(spec=Course)
    mock_course.id = 20
    mock_course.prerequisite_id = 10

    prereq_enrollment = MagicMock(spec=Enrollment)
    prereq_enrollment.status = EnrollmentStatus.APPROVED

    def query_side_effect(model):
        query_mock = MagicMock()
        if model == Course:
            query_mock.filter.return_value.first.return_value = mock_course
        elif model == Enrollment:
            query_mock.filter.return_value.first.return_value = prereq_enrollment
        return query_mock

    mock_db.query.side_effect = query_side_effect

    assert check_prerequisites(student_id=1, course_id=20, db=mock_db) is True


def test_check_prerequisites_prerequisite_not_satisfied() -> None:
    """Course with prerequisite NOT satisfied returns False."""
    mock_db = MagicMock()
    mock_course = MagicMock(spec=Course)
    mock_course.id = 20
    mock_course.prerequisite_id = 10

    def query_side_effect(model):
        query_mock = MagicMock()
        if model == Course:
            query_mock.filter.return_value.first.return_value = mock_course
        elif model == Enrollment:
            query_mock.filter.return_value.first.return_value = None
        return query_mock

    mock_db.query.side_effect = query_side_effect

    assert check_prerequisites(student_id=1, course_id=20, db=mock_db) is False


# ============================================================================
# Advisor Approval Workflow (PENDING -> APPROVED / REJECTED)
# ============================================================================


def test_advisor_approve_registration() -> None:
    """Test advisor approving a pending enrollment sets status to APPROVED."""
    mock_db = MagicMock()
    enrollment = MagicMock(spec=Enrollment)
    enrollment.id = 5
    enrollment.status = EnrollmentStatus.PENDING
    mock_db.query.return_value.filter.return_value.first.return_value = enrollment

    updated_enrollment = RegistrationService.update_enrollment_status(
        enrollment_id=5,
        new_status=EnrollmentStatus.APPROVED,
        db=mock_db,
    )

    assert updated_enrollment.status == EnrollmentStatus.APPROVED
    mock_db.commit.assert_called_once()


def test_advisor_reject_registration() -> None:
    """Test advisor rejecting a pending enrollment sets status to REJECTED."""
    mock_db = MagicMock()
    enrollment = MagicMock(spec=Enrollment)
    enrollment.id = 6
    enrollment.status = EnrollmentStatus.PENDING
    mock_db.query.return_value.filter.return_value.first.return_value = enrollment

    updated_enrollment = RegistrationService.update_enrollment_status(
        enrollment_id=6,
        new_status=EnrollmentStatus.REJECTED,
        db=mock_db,
    )

    assert updated_enrollment.status == EnrollmentStatus.REJECTED
    mock_db.commit.assert_called_once()


def test_advisor_update_nonexistent_enrollment_raises_value_error() -> None:
    """Test updating status of nonexistent enrollment raises ValueError."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError) as exc:
        RegistrationService.update_enrollment_status(
            enrollment_id=999,
            new_status=EnrollmentStatus.APPROVED,
            db=mock_db,
        )
    assert "Enrollment not found" in str(exc.value)
