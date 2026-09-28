"""
Student Success Analytics
SQLite Database Builder

Purpose
-------
Load the synthetic institutional CSV datasets into a local
SQLite database for SQL analysis and dashboard development.

This database is generated from the reproducible CSV source
files and is intentionally excluded from Git.

Important
---------
All data is synthetic and created for portfolio demonstration
purposes only.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path("data/synthetic")

DATABASE_DIR = DATA_DIR / "database"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_PATH = (
    DATABASE_DIR / "student_success.db"
)


# ============================================================
# Source tables
# ============================================================

SOURCE_TABLES = {
    "students": DATA_DIR / "students.csv",
    "courses": DATA_DIR / "courses.csv",
    "enrolments": DATA_DIR / "enrolments.csv",
    "attendance": DATA_DIR / "attendance.csv",
    "lms_activity": DATA_DIR / "lms_activity.csv",
    "assignment_submissions": (
        DATA_DIR / "assignment_submissions.csv"
    ),
    "assessments": DATA_DIR / "assessments.csv",
    "interventions": DATA_DIR / "interventions.csv",
    "simulation_truth": (
        DATA_DIR / "simulation_truth.csv"
    ),
}


# ============================================================
# Derived analytical tables
# ============================================================

RISK_TABLE = (
    DATA_DIR
    / "risk_reports"
    / "student_risk_scores.csv"
)

RISK_SUMMARY_TABLE = (
    DATA_DIR
    / "risk_reports"
    / "risk_summary.csv"
)

PROGRAMME_SUMMARY_TABLE = (
    DATA_DIR
    / "risk_reports"
    / "programme_risk_summary.csv"
)


# ============================================================
# Database initialization
# ============================================================

print("\n")
print("=" * 72)
print("STUDENT SUCCESS ANALYTICS — DATABASE BUILDER")
print("=" * 72)

print(
    f"\nDatabase: {DATABASE_PATH}"
)


connection = sqlite3.connect(
    DATABASE_PATH
)


try:

    # --------------------------------------------------------
    # Load source tables
    # --------------------------------------------------------

    print("\nLoading source tables...\n")

    for table_name, path in SOURCE_TABLES.items():

        if not path.exists():

            raise FileNotFoundError(
                f"Required source file not found: {path}"
            )

        dataframe = pd.read_csv(path)

        dataframe.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )

        print(
            f"✓ {table_name:<28} "
            f"{len(dataframe):>10,} rows"
        )


    # --------------------------------------------------------
    # Load analytical tables
    # --------------------------------------------------------

    print("\nLoading analytical outputs...\n")

    analytical_tables = {
        "student_risk_scores": RISK_TABLE,
        "risk_summary": RISK_SUMMARY_TABLE,
        "programme_risk_summary": (
            PROGRAMME_SUMMARY_TABLE
        ),
    }

    for table_name, path in analytical_tables.items():

        if not path.exists():

            raise FileNotFoundError(
                f"Analytical output not found: {path}"
            )

        dataframe = pd.read_csv(path)

        dataframe.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )

        print(
            f"✓ {table_name:<28} "
            f"{len(dataframe):>10,} rows"
        )


    # --------------------------------------------------------
    # Create indexes
    # --------------------------------------------------------

    print("\nCreating indexes...\n")

    indexes = [

        (
            "idx_students_student_id",
            "students",
            "student_id",
        ),

        (
            "idx_enrolments_student_id",
            "enrolments",
            "student_id",
        ),

        (
            "idx_enrolments_course_id",
            "enrolments",
            "course_id",
        ),

        (
            "idx_attendance_student_id",
            "attendance",
            "student_id",
        ),

        (
            "idx_attendance_course_id",
            "attendance",
            "course_id",
        ),

        (
            "idx_lms_student_id",
            "lms_activity",
            "student_id",
        ),

        (
            "idx_lms_course_id",
            "lms_activity",
            "course_id",
        ),

        (
            "idx_assignments_student_id",
            "assignment_submissions",
            "student_id",
        ),

        (
            "idx_assessments_student_id",
            "assessments",
            "student_id",
        ),

        (
            "idx_interventions_student_id",
            "interventions",
            "student_id",
        ),

        (
            "idx_risk_student_id",
            "student_risk_scores",
            "student_id",
        ),

        (
            "idx_risk_band",
            "student_risk_scores",
            "risk_band",
        ),

    ]


    for index_name, table_name, column_name in indexes:

        connection.execute(
            f"""
            CREATE INDEX IF NOT EXISTS
            {index_name}
            ON {table_name} ({column_name})
            """
        )

        print(
            f"✓ {index_name}"
        )


    # --------------------------------------------------------
    # Database metadata
    # --------------------------------------------------------

    metadata = pd.DataFrame(
        [
            {
                "database_name":
                    "student_success.db",
                "purpose":
                    "Synthetic student success analytics",
                "semester":
                    "Fall 2026",
                "source_type":
                    "Synthetic CSV datasets",
                "contains_real_student_data":
                    0,
            }
        ]
    )

    metadata.to_sql(
        "database_metadata",
        connection,
        if_exists="replace",
        index=False,
    )


    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    connection.commit()


    # --------------------------------------------------------
    # Verify tables
    # --------------------------------------------------------

    print("\n")
    print("-" * 72)
    print("DATABASE TABLES")
    print("-" * 72)

    tables = pd.read_sql_query(
        """
        SELECT
            name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """,
        connection,
    )

    print(
        tables.to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # Table row counts
    # --------------------------------------------------------

    print("\n")
    print("-" * 72)
    print("TABLE ROW COUNTS")
    print("-" * 72)

    table_names = tables["name"].tolist()

    for table_name in table_names:

        count_df = pd.read_sql_query(
            f"""
            SELECT COUNT(*) AS row_count
            FROM {table_name}
            """,
            connection,
        )

        row_count = int(
            count_df.iloc[0]["row_count"]
        )

        print(
            f"{table_name:<30} "
            f"{row_count:>10,}"
        )


    # --------------------------------------------------------
    # Basic integrity verification
    # --------------------------------------------------------

    print("\n")
    print("-" * 72)
    print("BASIC INTEGRITY CHECKS")
    print("-" * 72)


    student_count = pd.read_sql_query(
        """
        SELECT COUNT(*) AS count
        FROM students
        """,
        connection,
    ).iloc[0]["count"]


    risk_count = pd.read_sql_query(
        """
        SELECT COUNT(*) AS count
        FROM student_risk_scores
        """,
        connection,
    ).iloc[0]["count"]


    matching_ids = pd.read_sql_query(
        """
        SELECT COUNT(*) AS count
        FROM student_risk_scores r
        INNER JOIN students s
            ON r.student_id = s.student_id
        """,
        connection,
    ).iloc[0]["count"]


    print(
        f"Students:                 {int(student_count):,}"
    )

    print(
        f"Risk records:             {int(risk_count):,}"
    )

    print(
        f"Risk IDs matching SIS:    {int(matching_ids):,}"
    )


    if student_count == risk_count:

        print(
            "✓ One risk record exists for each student"
        )

    else:

        print(
            "⚠ Student/risk record counts differ"
        )


    if matching_ids == risk_count:

        print(
            "✓ Risk records have valid student IDs"
        )

    else:

        print(
            "⚠ Orphan risk records detected"
        )


finally:

    connection.close()


print("\n")
print("=" * 72)
print("DATABASE BUILD COMPLETE")
print("=" * 72)

print(
    f"\nSQLite database created at:"
)

print(
    DATABASE_PATH
)

print(
    "\nThe database is generated from the synthetic CSV "
    "source files and is excluded from Git."
)

print("=" * 72)