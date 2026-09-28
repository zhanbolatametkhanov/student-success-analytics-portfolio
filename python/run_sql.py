"""
Student Success Analytics
SQL Execution Runner

Purpose
-------
Execute portfolio SQL scripts against the generated SQLite database.

This provides a reproducible bridge between:

    SQLite database -> SQL -> analytical results

Important
---------
All data is synthetic and intended for demonstration purposes only.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)

SQL_DIR = PROJECT_ROOT / "sql"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "sql_results"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SQL scripts
# ============================================================

SQL_SCRIPTS = [
    "01_student_activity.sql",
    "02_risk_detection.sql",
    "03_intervention_outcomes.sql",
]


# ============================================================
# Helpers
# ============================================================

def execute_sql_script(
    connection: sqlite3.Connection,
    sql_path: Path,
) -> int:
    """
    Execute a SQL script and print basic execution information.

    Returns the number of SQL statements detected.
    """

    sql_text = sql_path.read_text(
        encoding="utf-8"
    )

    # Remove full-line comments.
    statements = []

    current_statement = []

    for line in sql_text.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("--"):
            continue

        current_statement.append(line)

        if stripped.endswith(";"):

            statement = "\n".join(
                current_statement
            ).strip()

            if statement:
                statements.append(statement)

            current_statement = []

    if current_statement:

        statement = "\n".join(
            current_statement
        ).strip()

        if statement:
            statements.append(statement)


    print(
        f"\nExecuting {sql_path.name}"
    )

    print(
        f"Statements detected: {len(statements)}"
    )

    return len(statements)


def export_query_result(
    connection: sqlite3.Connection,
    query: str,
    output_path: Path,
) -> None:
    """
    Execute one SELECT query and export the result as CSV.
    """

    result = pd.read_sql_query(
        query,
        connection,
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print(
        f"  ✓ {output_path.name}: "
        f"{len(result):,} rows"
    )


# ============================================================
# Main execution
# ============================================================

print("\n")
print("=" * 72)
print("STUDENT SUCCESS ANALYTICS — SQL EXECUTION")
print("=" * 72)

print(
    f"\nDatabase: {DATABASE_PATH}"
)


if not DATABASE_PATH.exists():

    raise FileNotFoundError(
        f"SQLite database not found: {DATABASE_PATH}"
    )


connection = sqlite3.connect(
    DATABASE_PATH
)


try:

    for sql_filename in SQL_SCRIPTS:

        sql_path = SQL_DIR / sql_filename

        if not sql_path.exists():

            raise FileNotFoundError(
                f"SQL script not found: {sql_path}"
            )

        execute_sql_script(
            connection,
            sql_path,
        )


    # --------------------------------------------------------
    # Portfolio result queries
    # --------------------------------------------------------

    print("\n")
    print("-" * 72)
    print("EXPORTING PORTFOLIO ANALYTICAL RESULTS")
    print("-" * 72)


    # Risk distribution
    export_query_result(
        connection,

        """
        SELECT
            risk_band,
            COUNT(*) AS students,
            ROUND(
                100.0 * COUNT(*) /
                (SELECT COUNT(*)
                 FROM student_risk_scores),
                2
            ) AS percentage
        FROM student_risk_scores
        GROUP BY risk_band
        ORDER BY
            CASE risk_band
                WHEN 'Low' THEN 1
                WHEN 'Moderate' THEN 2
                WHEN 'High' THEN 3
                WHEN 'Critical' THEN 4
            END
        """,

        OUTPUT_DIR
        / "risk_distribution_sql.csv",
    )


    # High / Critical students
    export_query_result(
        connection,

        """
        SELECT
            student_id,
            programme,
            school,
            risk_score,
            risk_band,
            risk_reasons,
            intervention_priority
        FROM student_risk_scores
        WHERE risk_band IN ('High', 'Critical')
        ORDER BY
            risk_score DESC,
            student_id
        """,

        OUTPUT_DIR
        / "priority_students_sql.csv",
    )


    # Programme-level analytics
    export_query_result(
        connection,

        """
        SELECT
            school,
            programme,
            students,
            average_risk_score,
            high_or_critical,
            high_or_critical_rate,
            average_attendance,
            average_score
        FROM programme_risk_summary
        ORDER BY
            average_risk_score DESC
        """,

        OUTPUT_DIR
        / "programme_risk_sql.csv",
    )


    # Intervention outcomes
    export_query_result(
        connection,

        """
        SELECT
            intervention_type,
            outcome,
            COUNT(*) AS intervention_count
        FROM interventions
        GROUP BY
            intervention_type,
            outcome
        ORDER BY
            intervention_type,
            intervention_count DESC
        """,

        OUTPUT_DIR
        / "intervention_outcomes_sql.csv",
    )


finally:

    connection.close()


print("\n")
print("=" * 72)
print("SQL EXECUTION COMPLETE")
print("=" * 72)

print(
    f"\nResults written to:"
)

print(
    OUTPUT_DIR
)

print("=" * 72)