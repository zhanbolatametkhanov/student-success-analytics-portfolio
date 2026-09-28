"""
Student Profile Analytical Dataset

Creates weekly student-level indicators that can be visualised
in the Student Profile page.

Synthetic data only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
)

OUTPUT_DIR = (
    DATA_DIR
    / "profile_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Load
# ============================================================

attendance = pd.read_csv(
    DATA_DIR / "attendance.csv"
)

lms = pd.read_csv(
    DATA_DIR / "lms_activity.csv"
)

assignments = pd.read_csv(
    DATA_DIR / "assignment_submissions.csv"
)

assessments = pd.read_csv(
    DATA_DIR / "assessments.csv"
)


# ============================================================
# Attendance by week
# ============================================================

attendance["present"] = (
    attendance["status"]
    == "PRESENT"
).astype(int)


weekly_attendance = (
    attendance
    .groupby(
        [
            "student_id",
            "week_number",
        ]
    )
    .agg(
        attendance_rate=(
            "present",
            "mean",
        ),
        attendance_events=(
            "present",
            "count",
        ),
    )
    .reset_index()
)


weekly_attendance[
    "attendance_rate"
] *= 100


# ============================================================
# LMS by week
# ============================================================

weekly_lms = (
    lms
    .groupby(
        [
            "student_id",
            "week_number",
        ]
    )
    .agg(
        login_count=(
            "login_count",
            "sum",
        ),
        minutes_active=(
            "minutes_active",
            "sum",
        ),
        assignment_views=(
            "assignment_views",
            "sum",
        ),
    )
    .reset_index()
)


# ============================================================
# Assignment submission by week
# ============================================================

assignments["submitted_numeric"] = pd.to_numeric(
    assignments["submitted"],
    errors="coerce",
)


weekly_assignments = (
    assignments
    .groupby(
        [
            "student_id",
            "week_number",
        ]
    )
    .agg(
        submission_rate=(
            "submitted_numeric",
            "mean",
        ),
        assignments=(
            "submitted_numeric",
            "count",
        ),
    )
    .reset_index()
)


weekly_assignments[
    "submission_rate"
] *= 100


# ============================================================
# Combine weekly indicators
# ============================================================

weekly_profile = (
    weekly_attendance
    .merge(
        weekly_lms,
        on=[
            "student_id",
            "week_number",
        ],
        how="outer",
    )
    .merge(
        weekly_assignments,
        on=[
            "student_id",
            "week_number",
        ],
        how="outer",
    )
)


weekly_profile = (
    weekly_profile
    .sort_values(
        [
            "student_id",
            "week_number",
        ]
    )
)


# ============================================================
# Assessment trajectory
# ============================================================

assessments[
    "assessment_date"
] = pd.to_datetime(
    assessments["assessment_date"],
    errors="coerce",
)


assessment_profile = (
    assessments
    .sort_values(
        [
            "student_id",
            "assessment_date",
        ]
    )
    .copy()
)


assessment_profile[
    "assessment_number"
] = (
    assessment_profile
    .groupby("student_id")
    .cumcount()
    + 1
)


# ============================================================
# Save
# ============================================================

weekly_path = (
    OUTPUT_DIR
    / "weekly_student_profile.csv"
)

assessment_path = (
    OUTPUT_DIR
    / "student_assessment_trajectory.csv"
)


weekly_profile.to_csv(
    weekly_path,
    index=False,
)

assessment_profile.to_csv(
    assessment_path,
    index=False,
)


print()
print("=" * 72)
print("STUDENT PROFILE ANALYTICS")
print("=" * 72)

print(
    f"\nWeekly records:       {len(weekly_profile):,}"
)

print(
    f"Assessment records:   {len(assessment_profile):,}"
)

print(
    f"\n✓ {weekly_path}"
)

print(
    f"✓ {assessment_path}"
)

print()
print("=" * 72)
print("PROFILE ANALYSIS COMPLETE")
print("=" * 72)
