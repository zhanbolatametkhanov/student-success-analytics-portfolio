"""
Centralised SQLite data-access layer.

The Streamlit interface should call functions in this module
rather than embedding database logic throughout the UI.

All data is synthetic portfolio data.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


def get_connection() -> sqlite3.Connection:
    """Open a read/write connection to the demonstration database."""

    if not DATABASE_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    return sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )


def query(
    sql: str,
    params: tuple = (),
) -> pd.DataFrame:
    """Execute a parameterised query and return a DataFrame."""

    connection = get_connection()

    try:

        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )

    finally:

        connection.close()


def load_risk_scores() -> pd.DataFrame:
    """Load student risk records."""

    return query(
        """
        SELECT *
        FROM student_risk_scores
        """
    )


def load_student(
    student_id: str,
) -> pd.DataFrame:
    """Load one synthetic student profile."""

    return query(
        """
        SELECT *
        FROM student_risk_scores
        WHERE student_id = ?
        """,
        (student_id,),
    )


def load_attendance(
    student_id: str,
) -> pd.DataFrame:
    """Load attendance history for one student."""

    return query(
        """
        SELECT
            student_id,
            course_id,
            attendance_date,
            week_number,
            status
        FROM attendance
        WHERE student_id = ?
        ORDER BY
            attendance_date
        """,
        (student_id,),
    )


def load_lms_activity(
    student_id: str,
) -> pd.DataFrame:
    """Load LMS activity history for one student."""

    return query(
        """
        SELECT
            student_id,
            course_id,
            activity_date,
            week_number,
            login_count,
            minutes_active,
            assignment_views
        FROM lms_activity
        WHERE student_id = ?
        ORDER BY
            activity_date
        """,
        (student_id,),
    )


def load_assessments(
    student_id: str,
) -> pd.DataFrame:
    """Load assessment history for one student."""

    return query(
        """
        SELECT
            student_id,
            course_id,
            assessment_type,
            assessment_date,
            score
        FROM assessments
        WHERE student_id = ?
        ORDER BY
            assessment_date
        """,
        (student_id,),
    )


def load_assignments(
    student_id: str,
) -> pd.DataFrame:
    """Load assignment history for one student."""

    return query(
        """
        SELECT
            student_id,
            course_id,
            assignment_date,
            week_number,
            submitted,
            days_late
        FROM assignment_submissions
        WHERE student_id = ?
        ORDER BY
            assignment_date
        """,
        (student_id,),
    )


def load_interventions(
    student_id: str,
) -> pd.DataFrame:
    """Load intervention history for one student."""

    return query(
        """
        SELECT
            intervention_id,
            student_id,
            risk_type,
            trigger_date,
            intervention_type,
            advisor,
            status,
            outcome
        FROM interventions
        WHERE student_id = ?
        ORDER BY
            trigger_date DESC
        """,
        (student_id,),
    )
