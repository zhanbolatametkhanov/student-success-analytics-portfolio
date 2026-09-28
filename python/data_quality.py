"""
Student Success Analytics
Data Quality Monitoring Module

Purpose
-------
Validate the synthetic institutional data used by the portfolio.

The checks cover:

- file availability
- row counts
- completeness
- uniqueness
- referential integrity
- domain validity
- date validity
- cross-table consistency

Important
---------
This is a demonstration environment using synthetic data only.
It is not connected to any real LMS, SIS, CRM or university database.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pandas as pd


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path("data/synthetic")
REPORT_DIR = DATA_DIR / "quality_reports"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


REQUIRED_FILES = [
    "students.csv",
    "courses.csv",
    "enrolments.csv",
    "attendance.csv",
    "lms_activity.csv",
    "assignment_submissions.csv",
    "assessments.csv",
    "interventions.csv",
    "simulation_truth.csv",
]


# ============================================================
# Reporting structure
# ============================================================

results: list[dict] = []


def add_result(
    check_id: str,
    category: str,
    table: str,
    check: str,
    passed: bool,
    details: str,
    severity: str = "INFO",
) -> None:
    """Add a structured check result."""

    results.append(
        {
            "check_id": check_id,
            "category": category,
            "table": table,
            "check": check,
            "status": "PASS" if passed else "FAIL",
            "severity": severity,
            "details": details,
        }
    )


# ============================================================
# Utility functions
# ============================================================

def load_table(filename: str) -> pd.DataFrame | None:
    """Load one CSV file safely."""

    path = DATA_DIR / filename

    if not path.exists():

        add_result(
            check_id=f"FILE-{filename}",
            category="Availability",
            table=filename,
            check="Required file exists",
            passed=False,
            details=f"Missing file: {path}",
            severity="CRITICAL",
        )

        return None

    try:

        dataframe = pd.read_csv(path)

        add_result(
            check_id=f"FILE-{filename}",
            category="Availability",
            table=filename,
            check="Required file exists and is readable",
            passed=True,
            details=f"{len(dataframe):,} rows loaded",
        )

        return dataframe

    except Exception as exc:

        add_result(
            check_id=f"FILE-{filename}",
            category="Availability",
            table=filename,
            check="CSV can be loaded",
            passed=False,
            details=str(exc),
            severity="CRITICAL",
        )

        return None


def check_required_columns(
    dataframe: pd.DataFrame,
    table_name: str,
    columns: list[str],
) -> None:
    """Check that required columns exist."""

    missing = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    add_result(
        check_id=f"COLUMNS-{table_name}",
        category="Schema",
        table=table_name,
        check="Required columns present",
        passed=len(missing) == 0,
        details=(
            "All required columns present"
            if not missing
            else f"Missing columns: {', '.join(missing)}"
        ),
        severity="CRITICAL" if missing else "INFO",
    )


def check_completeness(
    dataframe: pd.DataFrame,
    table_name: str,
    columns: list[str],
) -> None:
    """Check null values in critical columns."""

    for column in columns:

        null_count = int(
            dataframe[column].isna().sum()
        )

        total = len(dataframe)

        completeness = (
            100.0
            if total == 0
            else (1 - null_count / total) * 100
        )

        passed = null_count == 0

        add_result(
            check_id=f"COMP-{table_name}-{column}",
            category="Completeness",
            table=table_name,
            check=f"{column} contains no missing values",
            passed=passed,
            details=(
                f"{completeness:.2f}% complete; "
                f"{null_count:,} missing"
            ),
            severity="WARNING" if null_count else "INFO",
        )


def check_unique_key(
    dataframe: pd.DataFrame,
    table_name: str,
    key_columns: list[str],
) -> None:
    """Check whether a composite key is unique."""

    duplicates = dataframe.duplicated(
        subset=key_columns,
        keep=False,
    )

    duplicate_rows = int(duplicates.sum())

    duplicate_groups = int(
        dataframe.loc[duplicates, key_columns]
        .drop_duplicates()
        .shape[0]
    )

    passed = duplicate_rows == 0

    add_result(
        check_id=f"UNIQUE-{table_name}",
        category="Uniqueness",
        table=table_name,
        check=f"Unique key: {', '.join(key_columns)}",
        passed=passed,
        details=(
            "No duplicate keys"
            if passed
            else (
                f"{duplicate_rows:,} rows belong to "
                f"{duplicate_groups:,} duplicate key groups"
            )
        ),
        severity="WARNING" if not passed else "INFO",
    )


def check_foreign_key(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    child_table: str,
    parent_table: str,
    child_column: str,
    parent_column: str,
) -> None:
    """Check that every child key exists in the parent table."""

    child_values = (
        child_df[child_column]
        .dropna()
        .astype(str)
        .unique()
    )

    parent_values = (
        parent_df[parent_column]
        .dropna()
        .astype(str)
        .unique()
    )

    missing = sorted(
        set(child_values) - set(parent_values)
    )

    passed = len(missing) == 0

    preview = (
        "No orphan records"
        if passed
        else (
            f"{len(missing):,} missing parent keys; "
            f"examples: {missing[:5]}"
        )
    )

    add_result(
        check_id=(
            f"FK-{child_table}-"
            f"{child_column}-{parent_table}"
        ),
        category="Referential integrity",
        table=child_table,
        check=(
            f"{child_column} values exist in "
            f"{parent_table}.{parent_column}"
        ),
        passed=passed,
        details=preview,
        severity="CRITICAL" if not passed else "INFO",
    )


def check_numeric_range(
    dataframe: pd.DataFrame,
    table_name: str,
    column: str,
    minimum: float,
    maximum: float,
) -> None:
    """Validate numeric values against a permitted range."""

    numeric = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )

    invalid = numeric.notna() & (
        (numeric < minimum)
        | (numeric > maximum)
    )

    invalid_count = int(invalid.sum())

    passed = invalid_count == 0

    add_result(
        check_id=f"RANGE-{table_name}-{column}",
        category="Validity",
        table=table_name,
        check=f"{column} between {minimum} and {maximum}",
        passed=passed,
        details=(
            f"All non-null values are within range"
            if passed
            else f"{invalid_count:,} invalid values"
        ),
        severity="WARNING" if not passed else "INFO",
    )


def check_allowed_values(
    dataframe: pd.DataFrame,
    table_name: str,
    column: str,
    allowed_values: set[str],
) -> None:
    """Validate categorical values."""

    observed = set(
        dataframe[column]
        .dropna()
        .astype(str)
        .unique()
    )

    invalid = sorted(
        observed - allowed_values
    )

    passed = len(invalid) == 0

    add_result(
        check_id=f"DOMAIN-{table_name}-{column}",
        category="Validity",
        table=table_name,
        check=f"{column} uses permitted values",
        passed=passed,
        details=(
            "All values valid"
            if passed
            else f"Unexpected values: {invalid}"
        ),
        severity="WARNING" if not passed else "INFO",
    )


def check_dates(
    dataframe: pd.DataFrame,
    table_name: str,
    column: str,
) -> None:
    """Check that a date column contains parseable dates."""

    parsed = pd.to_datetime(
        dataframe[column],
        errors="coerce",
    )

    invalid_count = int(
        parsed.isna().sum()
    )

    passed = invalid_count == 0

    add_result(
        check_id=f"DATE-{table_name}-{column}",
        category="Validity",
        table=table_name,
        check=f"{column} contains valid dates",
        passed=passed,
        details=(
            "All values parse as dates"
            if passed
            else f"{invalid_count:,} invalid or missing dates"
        ),
        severity="WARNING" if not passed else "INFO",
    )


# ============================================================
# Load datasets
# ============================================================

tables = {
    filename: load_table(filename)
    for filename in REQUIRED_FILES
}


students = tables["students.csv"]
courses = tables["courses.csv"]
enrolments = tables["enrolments.csv"]
attendance = tables["attendance.csv"]
lms = tables["lms_activity.csv"]
assignments = tables["assignment_submissions.csv"]
assessments = tables["assessments.csv"]
interventions = tables["interventions.csv"]
simulation_truth = tables["simulation_truth.csv"]


# ============================================================
# Schema checks
# ============================================================

if students is not None:

    check_required_columns(
        students,
        "students",
        [
            "student_id",
            "programme_code",
            "programme",
            "school",
            "year_of_study",
            "enrolment_status",
        ],
    )


if courses is not None:

    check_required_columns(
        courses,
        "courses",
        [
            "course_id",
            "course_name",
            "credits",
            "department_code",
            "semester",
        ],
    )


if enrolments is not None:

    check_required_columns(
        enrolments,
        "enrolments",
        [
            "student_id",
            "course_id",
            "semester",
            "status",
        ],
    )


if attendance is not None:

    check_required_columns(
        attendance,
        "attendance",
        [
            "student_id",
            "course_id",
            "attendance_date",
            "week_number",
            "status",
        ],
    )


if lms is not None:

    check_required_columns(
        lms,
        "lms_activity",
        [
            "student_id",
            "course_id",
            "activity_date",
            "week_number",
            "login_count",
            "minutes_active",
            "assignment_views",
        ],
    )


if assignments is not None:

    check_required_columns(
        assignments,
        "assignment_submissions",
        [
            "student_id",
            "course_id",
            "assignment_date",
            "week_number",
            "submitted",
            "days_late",
        ],
    )


if assessments is not None:

    check_required_columns(
        assessments,
        "assessments",
        [
            "student_id",
            "course_id",
            "assessment_type",
            "assessment_date",
            "score",
        ],
    )


if interventions is not None:

    check_required_columns(
        interventions,
        "interventions",
        [
            "intervention_id",
            "student_id",
            "risk_type",
            "trigger_date",
            "intervention_type",
            "advisor",
            "status",
            "outcome",
        ],
    )


# ============================================================
# Completeness checks
# ============================================================

if students is not None:

    check_completeness(
        students,
        "students",
        [
            "student_id",
            "programme_code",
            "programme",
            "school",
            "year_of_study",
            "enrolment_status",
        ],
    )


if courses is not None:

    check_completeness(
        courses,
        "courses",
        [
            "course_id",
            "course_name",
            "credits",
            "department_code",
            "semester",
        ],
    )


if enrolments is not None:

    check_completeness(
        enrolments,
        "enrolments",
        [
            "student_id",
            "course_id",
            "semester",
            "status",
        ],
    )


if attendance is not None:

    check_completeness(
        attendance,
        "attendance",
        [
            "student_id",
            "course_id",
            "attendance_date",
            "status",
        ],
    )


if lms is not None:

    check_completeness(
        lms,
        "lms_activity",
        [
            "student_id",
            "course_id",
            "activity_date",
            "login_count",
            "minutes_active",
            "assignment_views",
        ],
    )


if assignments is not None:

    check_completeness(
        assignments,
        "assignment_submissions",
        [
            "student_id",
            "course_id",
            "assignment_date",
            "submitted",
            "days_late",
        ],
    )


if assessments is not None:

    check_completeness(
        assessments,
        "assessments",
        [
            "student_id",
            "course_id",
            "assessment_type",
            "assessment_date",
            "score",
        ],
    )


if interventions is not None:

    check_completeness(
        interventions,
        "interventions",
        [
            "intervention_id",
            "student_id",
            "risk_type",
            "trigger_date",
            "intervention_type",
            "advisor",
            "status",
            "outcome",
        ],
    )


# ============================================================
# Uniqueness checks
# ============================================================

if students is not None:

    check_unique_key(
        students,
        "students",
        ["student_id"],
    )


if courses is not None:

    check_unique_key(
        courses,
        "courses",
        ["course_id"],
    )


if enrolments is not None:

    check_unique_key(
        enrolments,
        "enrolments",
        [
            "student_id",
            "course_id",
            "semester",
        ],
    )


if attendance is not None:

    check_unique_key(
        attendance,
        "attendance",
        [
            "student_id",
            "course_id",
            "attendance_date",
        ],
    )


if lms is not None:

    check_unique_key(
        lms,
        "lms_activity",
        [
            "student_id",
            "course_id",
            "activity_date",
        ],
    )


if assignments is not None:

    check_unique_key(
        assignments,
        "assignment_submissions",
        [
            "student_id",
            "course_id",
            "assignment_date",
        ],
    )


if assessments is not None:

    check_unique_key(
        assessments,
        "assessments",
        [
            "student_id",
            "course_id",
            "assessment_type",
        ],
    )


if interventions is not None:

    check_unique_key(
        interventions,
        "interventions",
        ["intervention_id"],
    )


# ============================================================
# Referential integrity
# ============================================================

if students is not None and enrolments is not None:

    check_foreign_key(
        enrolments,
        students,
        "enrolments",
        "students",
        "student_id",
        "student_id",
    )


if courses is not None and enrolments is not None:

    check_foreign_key(
        enrolments,
        courses,
        "enrolments",
        "courses",
        "course_id",
        "course_id",
    )


if students is not None and attendance is not None:

    check_foreign_key(
        attendance,
        students,
        "attendance",
        "students",
        "student_id",
        "student_id",
    )


if courses is not None and attendance is not None:

    check_foreign_key(
        attendance,
        courses,
        "attendance",
        "courses",
        "course_id",
        "course_id",
    )


if students is not None and lms is not None:

    check_foreign_key(
        lms,
        students,
        "lms_activity",
        "students",
        "student_id",
        "student_id",
    )


if courses is not None and lms is not None:

    check_foreign_key(
        lms,
        courses,
        "lms_activity",
        "courses",
        "course_id",
        "course_id",
    )


if students is not None and assignments is not None:

    check_foreign_key(
        assignments,
        students,
        "assignment_submissions",
        "students",
        "student_id",
        "student_id",
    )


if courses is not None and assignments is not None:

    check_foreign_key(
        assignments,
        courses,
        "assignment_submissions",
        "courses",
        "course_id",
        "course_id",
    )


if students is not None and assessments is not None:

    check_foreign_key(
        assessments,
        students,
        "assessments",
        "students",
        "student_id",
        "student_id",
    )


if courses is not None and assessments is not None:

    check_foreign_key(
        assessments,
        courses,
        "assessments",
        "courses",
        "course_id",
        "course_id",
    )


if students is not None and interventions is not None:

    check_foreign_key(
        interventions,
        students,
        "interventions",
        "students",
        "student_id",
        "student_id",
    )


# ============================================================
# Validity checks
# ============================================================

if students is not None:

    check_numeric_range(
        students,
        "students",
        "year_of_study",
        1,
        4,
    )

    check_allowed_values(
        students,
        "students",
        "enrolment_status",
        {"Active"},
    )


if courses is not None:

    check_numeric_range(
        courses,
        "courses",
        "credits",
        1,
        30,
    )


if attendance is not None:

    check_allowed_values(
        attendance,
        "attendance",
        "status",
        {
            "PRESENT",
            "ABSENT",
        },
    )

    check_numeric_range(
        attendance,
        "attendance",
        "week_number",
        1,
        10,
    )


if lms is not None:

    check_numeric_range(
        lms,
        "lms_activity",
        "login_count",
        0,
        100,
    )

    check_numeric_range(
        lms,
        "lms_activity",
        "minutes_active",
        0,
        2000,
    )

    check_numeric_range(
        lms,
        "lms_activity",
        "assignment_views",
        0,
        100,
    )


if assignments is not None:

    check_numeric_range(
        assignments,
        "assignment_submissions",
        "submitted",
        0,
        1,
    )

    check_numeric_range(
        assignments,
        "assignment_submissions",
        "days_late",
        0,
        365,
    )


if assessments is not None:

    check_allowed_values(
        assessments,
        "assessments",
        "assessment_type",
        {
            "Quiz",
            "Midterm",
            "Assignment",
        },
    )

    check_numeric_range(
        assessments,
        "assessments",
        "score",
        0,
        100,
    )


if interventions is not None:

    check_allowed_values(
        interventions,
        "interventions",
        "risk_type",
        {
            "Attendance",
            "Academic performance",
            "LMS engagement",
            "Multiple indicators",
        },
    )

    check_allowed_values(
        interventions,
        "interventions",
        "status",
        {
            "Pending",
            "In progress",
            "Completed",
        },
    )


# ============================================================
# Date checks
# ============================================================

if attendance is not None:

    check_dates(
        attendance,
        "attendance",
        "attendance_date",
    )


if lms is not None:

    check_dates(
        lms,
        "lms_activity",
        "activity_date",
    )


if assignments is not None:

    check_dates(
        assignments,
        "assignment_submissions",
        "assignment_date",
    )


if assessments is not None:

    check_dates(
        assessments,
        "assessments",
        "assessment_date",
    )


if interventions is not None:

    check_dates(
        interventions,
        "interventions",
        "trigger_date",
    )


# ============================================================
# Cross-table consistency
# ============================================================

if enrolments is not None and attendance is not None:

    attendance_pairs = set(
        zip(
            attendance["student_id"].astype(str),
            attendance["course_id"].astype(str),
        )
    )

    enrolment_pairs = set(
        zip(
            enrolments["student_id"].astype(str),
            enrolments["course_id"].astype(str),
        )
    )

    orphan_pairs = attendance_pairs - enrolment_pairs

    add_result(
        check_id="CONSISTENCY-ATTENDANCE-ENROLMENT",
        category="Consistency",
        table="attendance",
        check="Attendance belongs to a valid enrolment",
        passed=len(orphan_pairs) == 0,
        details=(
            "All attendance combinations match enrolments"
            if len(orphan_pairs) == 0
            else (
                f"{len(orphan_pairs):,} "
                "student/course combinations not found "
                "in enrolments"
            )
        ),
        severity="WARNING" if orphan_pairs else "INFO",
    )


if lms is not None and enrolments is not None:

    lms_pairs = set(
        zip(
            lms["student_id"].astype(str),
            lms["course_id"].astype(str),
        )
    )

    enrolment_pairs = set(
        zip(
            enrolments["student_id"].astype(str),
            enrolments["course_id"].astype(str),
        )
    )

    orphan_pairs = lms_pairs - enrolment_pairs

    add_result(
        check_id="CONSISTENCY-LMS-ENROLMENT",
        category="Consistency",
        table="lms_activity",
        check="LMS activity belongs to a valid enrolment",
        passed=len(orphan_pairs) == 0,
        details=(
            "All LMS combinations match enrolments"
            if len(orphan_pairs) == 0
            else (
                f"{len(orphan_pairs):,} "
                "student/course combinations not found "
                "in enrolments"
            )
        ),
        severity="WARNING" if orphan_pairs else "INFO",
    )


# ============================================================
# Build report
# ============================================================

report_df = pd.DataFrame(results)


total_checks = len(report_df)

passed_checks = int(
    (report_df["status"] == "PASS").sum()
)

failed_checks = total_checks - passed_checks

quality_percentage = (
    100.0
    if total_checks == 0
    else passed_checks / total_checks * 100
)


# ============================================================
# Summary by category
# ============================================================

category_summary = (
    report_df
    .groupby("category")
    .agg(
        checks=("status", "count"),
        passed=("status", lambda x: (x == "PASS").sum()),
        failed=("status", lambda x: (x == "FAIL").sum()),
    )
    .reset_index()
)

category_summary["pass_rate"] = (
    category_summary["passed"]
    / category_summary["checks"]
    * 100
)


# ============================================================
# Save reports
# ============================================================

report_path = (
    REPORT_DIR / "data_quality_report.csv"
)

summary_path = (
    REPORT_DIR / "data_quality_summary.csv"
)

report_df.to_csv(
    report_path,
    index=False,
)

category_summary.to_csv(
    summary_path,
    index=False,
)


# ============================================================
# Console output
# ============================================================

print("\n")
print("=" * 72)
print("STUDENT SUCCESS ANALYTICS — DATA QUALITY MONITOR")
print("=" * 72)

print(
    f"\nChecks performed: {total_checks:,}"
)

print(
    f"Checks passed:    {passed_checks:,}"
)

print(
    f"Checks failed:    {failed_checks:,}"
)

print(
    f"Prototype quality index: {quality_percentage:.1f}%"
)

print("\n" + "-" * 72)
print("CATEGORY SUMMARY")
print("-" * 72)

print(
    category_summary.to_string(
        index=False,
        formatters={
            "pass_rate": "{:.1f}%".format,
        },
    )
)

print("\n" + "-" * 72)
print("FAILED CHECKS")
print("-" * 72)

failed_df = report_df[
    report_df["status"] == "FAIL"
]

if failed_df.empty:

    print("No failed checks detected.")

else:

    display_columns = [
        "category",
        "table",
        "check",
        "details",
    ]

    print(
        failed_df[
            display_columns
        ].to_string(index=False)
    )


print("\n" + "-" * 72)
print("REPORT FILES")
print("-" * 72)

print(
    f"Detailed report: {report_path}"
)

print(
    f"Category summary: {summary_path}"
)

print("\nData-quality validation complete.")
print("=" * 72)