"""
Project integrity and regression tests.

These tests validate the synthetic portfolio environment.

They deliberately test properties of the analytical pipeline rather
than testing implementation details.

All data is synthetic.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
)

RISK_DIR = (
    DATA_DIR
    / "risk_reports"
)

PROFILE_DIR = (
    DATA_DIR
    / "profile_reports"
)

QUALITY_DIR = (
    DATA_DIR
    / "quality_reports"
)

DATABASE_PATH = (
    DATA_DIR
    / "database"
    / "student_success.db"
)


# ============================================================
# Helper
# ============================================================

def read_csv(
    path: Path,
) -> pd.DataFrame:
    """Read a CSV and fail clearly if it does not exist."""

    assert path.exists(), (
        f"Expected file does not exist: {path}"
    )

    return pd.read_csv(path)


# ============================================================
# Source data
# ============================================================

def test_source_students_count():

    df = read_csv(
        DATA_DIR / "students.csv"
    )

    assert len(df) == 2500

    assert (
        df["student_id"].nunique()
        == 2500
    )


def test_source_courses_count():

    df = read_csv(
        DATA_DIR / "courses.csv"
    )

    assert len(df) == 18


def test_source_enrolments_count():

    df = read_csv(
        DATA_DIR / "enrolments.csv"
    )

    assert len(df) == 12511


def test_source_attendance_count():

    df = read_csv(
        DATA_DIR / "attendance.csv"
    )

    assert len(df) == 125125


def test_source_lms_count():

    df = read_csv(
        DATA_DIR / "lms_activity.csv"
    )

    assert len(df) == 125110


def test_source_assignments_count():

    df = read_csv(
        DATA_DIR / "assignment_submissions.csv"
    )

    assert len(df) == 125110


def test_source_assessments_count():

    df = read_csv(
        DATA_DIR / "assessments.csv"
    )

    assert len(df) == 37533


# ============================================================
# Risk output
# ============================================================

def test_risk_output_has_one_record_per_student():

    df = read_csv(
        RISK_DIR
        / "student_risk_scores.csv"
    )

    assert len(df) == 2500

    assert (
        df["student_id"].nunique()
        == 2500
    )


def test_risk_scores_are_valid():

    df = read_csv(
        RISK_DIR
        / "student_risk_scores.csv"
    )

    assert (
        df["risk_score"]
        .between(0, 100)
        .all()
    )


def test_risk_bands_are_valid():

    df = read_csv(
        RISK_DIR
        / "student_risk_scores.csv"
    )

    allowed = {
        "Low",
        "Moderate",
        "High",
        "Critical",
    }

    assert set(
        df["risk_band"].unique()
    ).issubset(
        allowed
    )


# ============================================================
# Model evaluation
# ============================================================

def test_model_metrics_exist():

    df = read_csv(
        RISK_DIR
        / "model_metrics.csv"
    )

    required_metrics = {
        "Accuracy",
        "Precision",
        "Recall",
        "Specificity",
        "F1",
        "Exact four-band agreement",
    }

    assert required_metrics.issubset(
        set(df["metric"])
    )


def test_confusion_matrix_totals_2500():

    df = read_csv(
        RISK_DIR
        / "model_confusion_matrix.csv"
    )

    assert (
        df["count"].sum()
        == 2500
    )


def test_threshold_analysis_exists():

    df = read_csv(
        RISK_DIR
        / "threshold_analysis.csv"
    )

    expected_thresholds = {
        20,
        30,
        40,
        50,
        60,
        70,
        80,
    }

    assert expected_thresholds == set(
        df["threshold"]
    )


# ============================================================
# Data quality
# ============================================================

def test_quality_report_count():

    df = read_csv(
        QUALITY_DIR
        / "data_quality_report.csv"
    )

    assert len(df) == 100


def test_quality_summary_count():

    df = read_csv(
        QUALITY_DIR
        / "data_quality_summary.csv"
    )

    assert len(df) == 7


# ============================================================
# Student profile
# ============================================================

def test_weekly_profile_shape():

    df = read_csv(
        PROFILE_DIR
        / "weekly_student_profile.csv"
    )

    assert len(df) == 25000

    assert (
        df["student_id"].nunique()
        == 2500
    )

    assert (
        df["week_number"].nunique()
        == 10
    )


def test_weekly_profile_covers_weeks_one_to_ten():

    df = read_csv(
        PROFILE_DIR
        / "weekly_student_profile.csv"
    )

    weeks = set(
        df["week_number"]
        .dropna()
        .astype(int)
        .unique()
    )

    assert weeks == set(
        range(1, 11)
    )


# ============================================================
# SQLite
# ============================================================

@pytest.mark.skipif(
    not DATABASE_PATH.exists(),
    reason="SQLite database not available",
)
def test_database_student_count():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM students
        """
    ).fetchone()[0]

    connection.close()

    assert result == 2500


@pytest.mark.skipif(
    not DATABASE_PATH.exists(),
    reason="SQLite database not available",
)
def test_database_risk_count():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM student_risk_scores
        """
    ).fetchone()[0]

    connection.close()

    assert result == 2500


@pytest.mark.skipif(
    not DATABASE_PATH.exists(),
    reason="SQLite database not available",
)
def test_database_profile_count():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM weekly_student_profile
        """
    ).fetchone()[0]

    connection.close()

    assert result == 25000


@pytest.mark.skipif(
    not DATABASE_PATH.exists(),
    reason="SQLite database not available",
)
def test_database_integration_tables():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
    }

    connection.close()

    expected = {
        "integration_health",
        "integration_events",
    }

    assert expected.issubset(
        tables
    )
