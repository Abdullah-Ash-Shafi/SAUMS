"""Behavioral Design Pattern: Strategy Pattern for Grading.

This module implements the Strategy Pattern (Behavioral) to allow flexible, interchangeable
grading algorithms (e.g., standard RUET degree grading vs. pass/fail grading).
Different grading systems can be injected into the result processing pipeline
at runtime without modifying core evaluation or service code.
"""
from abc import ABC, abstractmethod


class GradingStrategy(ABC):
    """Abstract Strategy interface declaring the contract for grade calculation algorithms."""

    @abstractmethod
    def calculate_grade(self, total_marks: float) -> tuple[str, float]:
        """Map total marks to a letter grade and Grade Point Average (GPA).

        Args:
            total_marks: Combined continuous assessment and final exam score (0.0 to 100.0).

        Returns:
            A tuple of (letter_grade: str, gpa: float).

        Raises:
            ValueError: If total_marks is invalid (< 0.0 or > 100.0).
        """
        pass


class StandardRUETGradingStrategy(GradingStrategy):
    """Concrete Strategy implementing the Standard RUET Letter Grading & CGPA system.

    Grading Scale:
        - 80% and above   : A+ (4.00)
        - 75% to < 80%    : A  (3.75)
        - 70% to < 75%    : A- (3.50)
        - 65% to < 70%    : B+ (3.25)
        - 60% to < 65%    : B  (3.00)
        - 55% to < 60%    : B- (2.75)
        - 50% to < 55%    : C+ (2.50)
        - 45% to < 50%    : C  (2.25)
        - 40% to < 45%    : D  (2.00)
        - Below 40%       : F  (0.00)
    """

    def calculate_grade(self, total_marks: float) -> tuple[str, float]:
        """Calculate letter grade and GPA under the standard RUET grading scale."""
        if total_marks < 0.0 or total_marks > 100.0:
            raise ValueError(
                f"Invalid marks: Total marks {total_marks} must be between 0 and 100."
            )

        if total_marks >= 80.0:
            return "A+", 4.00
        elif total_marks >= 75.0:
            return "A", 3.75
        elif total_marks >= 70.0:
            return "A-", 3.50
        elif total_marks >= 65.0:
            return "B+", 3.25
        elif total_marks >= 60.0:
            return "B", 3.00
        elif total_marks >= 55.0:
            return "B-", 2.75
        elif total_marks >= 50.0:
            return "C+", 2.50
        elif total_marks >= 45.0:
            return "C", 2.25
        elif total_marks >= 40.0:
            return "D", 2.00
        else:
            return "F", 0.00


class PassFailGradingStrategy(GradingStrategy):
    """Concrete Strategy implementing a Binary Pass/Fail grading scale.

    Commonly used for non-credit seminars, thesis clearances, or audit courses.
        - 40% and above : P (4.00)
        - Below 40%     : F (0.00)
    """

    def calculate_grade(self, total_marks: float) -> tuple[str, float]:
        """Calculate Pass/Fail grade."""
        if total_marks < 0.0 or total_marks > 100.0:
            raise ValueError(
                f"Invalid marks: Total marks {total_marks} must be between 0 and 100."
            )

        if total_marks >= 40.0:
            return "P", 4.00
        else:
            return "F", 0.00


def calculateGPA(
    ca_marks: float,
    final_marks: float,
    strategy: GradingStrategy | None = None,
) -> tuple[str, float]:
    """Calculate letter grade and GPA from CA and final marks using injected Strategy.

    Equivalence Partitioning & Boundary-Value Analysis:
        - Negative marks (< 0): Invalid -> ValueError
        - Marks > 100: Invalid -> ValueError
        - 0 to 39: F (0.00)
        - 40 to 79: Passing range (D to A)
        - 80 to 100: A+ (4.00)

    Args:
        ca_marks: Continuous Assessment score (0.0 to 40.0).
        final_marks: Final exam score (0.0 to 60.0).
        strategy: Injected GradingStrategy (defaults to StandardRUETGradingStrategy).

    Returns:
        A tuple of (letter_grade: str, gpa: float).

    Raises:
        ValueError: If marks are outside valid bounds (< 0 or > 100).
    """
    if ca_marks < 0.0 or final_marks < 0.0:
        raise ValueError(
            f"Invalid marks: CA ({ca_marks}) and Final ({final_marks}) marks cannot be negative."
        )

    total_marks = round(ca_marks + final_marks, 2)
    if total_marks > 100.0:
        raise ValueError(
            f"Invalid marks: Combined total marks {total_marks} exceeds maximum limit of 100."
        )

    grading_strategy: GradingStrategy = strategy or StandardRUETGradingStrategy()
    return grading_strategy.calculate_grade(total_marks)
