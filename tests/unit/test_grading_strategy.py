"""Unit tests for Grading Strategy and calculateGPA (TDD First).

Tests Equivalence Partitioning (EP) and Boundary-Value Analysis (BVA) for calculateGPA:
- Invalid low: -5 (raises ValueError)
- Failing boundary: 39 ("F", 0.00)
- Passing boundary: 40 ("D", 2.00)
- Top grade boundary: 80 ("A+", 4.00)
- Invalid high: 105 (raises ValueError)

Also tests Strategy Pattern:
- StandardRUETGradingStrategy
- PassFailGradingStrategy
- Dynamic strategy injection
"""
import pytest

from suams.results.grading import (
    GradingStrategy,
    StandardRUETGradingStrategy,
    PassFailGradingStrategy,
    calculateGPA,
)


# ============================================================================
# Equivalence Partitioning & Boundary-Value Analysis (BVA) Tests
# ============================================================================


def test_calculate_gpa_bva_invalid_negative() -> None:
    """BVA Test: Total marks -5 (below 0) must raise ValueError."""
    with pytest.raises(ValueError) as exc:
        calculateGPA(ca_marks=-5.0, final_marks=0.0)
    assert "Invalid marks" in str(exc.value)


def test_calculate_gpa_bva_39_fail() -> None:
    """BVA Test: Total marks 39 (boundary of fail) -> ('F', 0.00)."""
    # e.g., CA = 15, Final = 24 -> Total = 39
    grade, gpa = calculateGPA(ca_marks=15.0, final_marks=24.0)
    assert grade == "F"
    assert gpa == 0.00


def test_calculate_gpa_bva_40_pass() -> None:
    """BVA Test: Total marks 40 (exact pass threshold) -> ('D', 2.00)."""
    # e.g., CA = 16, Final = 24 -> Total = 40
    grade, gpa = calculateGPA(ca_marks=16.0, final_marks=24.0)
    assert grade == "D"
    assert gpa == 2.00


def test_calculate_gpa_bva_80_top_grade() -> None:
    """BVA Test: Total marks 80 (exact A+ threshold) -> ('A+', 4.00)."""
    # e.g., CA = 32, Final = 48 -> Total = 80
    grade, gpa = calculateGPA(ca_marks=32.0, final_marks=48.0)
    assert grade == "A+"
    assert gpa == 4.00


def test_calculate_gpa_bva_invalid_over_hundred() -> None:
    """BVA Test: Total marks 105 (exceeds 100) must raise ValueError."""
    with pytest.raises(ValueError) as exc:
        calculateGPA(ca_marks=45.0, final_marks=60.0)
    assert "Invalid marks" in str(exc.value)


# ============================================================================
# Strategy Pattern Tests
# ============================================================================


def test_standard_ruet_grading_strategy_intermediate_grades() -> None:
    """Test full RUET grading scale mapping in StandardRUETGradingStrategy."""
    strategy = StandardRUETGradingStrategy()

    assert strategy.calculate_grade(85.0) == ("A+", 4.00)
    assert strategy.calculate_grade(76.0) == ("A", 3.75)
    assert strategy.calculate_grade(71.0) == ("A-", 3.50)
    assert strategy.calculate_grade(66.0) == ("B+", 3.25)
    assert strategy.calculate_grade(61.0) == ("B", 3.00)
    assert strategy.calculate_grade(56.0) == ("B-", 2.75)
    assert strategy.calculate_grade(51.0) == ("C+", 2.50)
    assert strategy.calculate_grade(46.0) == ("C", 2.25)
    assert strategy.calculate_grade(41.0) == ("D", 2.00)
    assert strategy.calculate_grade(25.0) == ("F", 0.00)


def test_pass_fail_grading_strategy() -> None:
    """Test PassFailGradingStrategy produces Pass/Fail results."""
    pf_strategy = PassFailGradingStrategy()

    assert pf_strategy.calculate_grade(40.0) == ("P", 4.00)
    assert pf_strategy.calculate_grade(85.0) == ("P", 4.00)
    assert pf_strategy.calculate_grade(39.9) == ("F", 0.00)

    with pytest.raises(ValueError):
        pf_strategy.calculate_grade(-1.0)

    with pytest.raises(ValueError):
        pf_strategy.calculate_grade(101.0)


def test_dynamic_grading_strategy_injection() -> None:
    """Test injecting different grading strategies into calculateGPA."""
    ruet_strategy = StandardRUETGradingStrategy()
    pf_strategy = PassFailGradingStrategy()

    # Standard RUET grading gives A+ for 85
    grade_ruet, gpa_ruet = calculateGPA(ca_marks=35.0, final_marks=50.0, strategy=ruet_strategy)
    assert grade_ruet == "A+"
    assert gpa_ruet == 4.00

    # Injected Pass/Fail strategy gives P for 85
    grade_pf, gpa_pf = calculateGPA(ca_marks=35.0, final_marks=50.0, strategy=pf_strategy)
    assert grade_pf == "P"
    assert gpa_pf == 4.00
