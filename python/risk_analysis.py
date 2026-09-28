"""
Student Success Analytics
Transparent Early-Warning Risk Analysis

Purpose
-------
Transform validated synthetic institutional data into
student-level academic risk indicators.

The model is intentionally transparent and explainable.

It is a portfolio prototype only.

IMPORTANT
---------
The scoring framework and thresholds in this file are
demonstration assumptions. They are NOT Nazarbayev
University's actual RISE methodology or institutional
risk thresholds.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path("data/synthetic")

OUTPUT_DIR = (
    DATA_DIR / "risk_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SEMESTER_WEEKS = 10


# ============================================================
# Risk-band thresholds
# ============================================================

RISK_BANDS = [
    (0, 29, "Low"),
    (30, 59, "Moderate"),
    (60, 79, "High"),
    (80, 100, "Critical"),
]


# ============================================================
# Helper functions
# ============================================================

def risk_band(score: float) -> str:
    """Convert a 0-100 risk score into a risk band."""

    for minimum, maximum, label in RISK_BANDS:

        if minimum <= score <= maximum:
            return label

    if score < 0:
        return "Low"

    return "Critical"


def safe_mean(series: pd.Series) -> float:
    """Return a numeric mean or zero when no observations exist."""

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.0

    return float(values.mean())


def safe_sum(series: pd.Series) -> float:
    """Return a numeric sum or zero."""

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(0)

    return float(values.sum())


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    """Keep a score inside a specified range."""

    return float(
        np.clip(
            value,
            minimum,
            maximum,
        )
    )


# ============================================================
# Load data
# ============================================================

students = pd.read_csv(
    DATA_DIR / "students.csv"
)

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
# Convert dates
# ============================================================

attendance["attendance_date"] = pd.to_datetime(
    attendance["attendance_date"],
    errors="coerce",
)

lms["activity_date"] = pd.to_datetime(
    lms["activity_date"],
    errors="coerce",
)

assignments["assignment_date"] = pd.to_datetime(
    assignments["assignment_date"],
    errors="coerce",
)

assessments["assessment_date"] = pd.to_datetime(
    assessments["assessment_date"],
    errors="coerce",
)


# ============================================================
# 1. Attendance indicators
# ============================================================

attendance_clean = attendance.drop_duplicates(
    subset=[
        "student_id",
        "course_id",
        "attendance_date",
    ]
).copy()

attendance_summary = (
    attendance_clean
    .groupby("student_id")
    .agg(
        attendance_events=(
            "status",
            "count",
        ),
        absences=(
            "status",
            lambda x: (x == "ABSENT").sum(),
        ),
    )
    .reset_index()
)

attendance_summary["attendance_rate"] = (
    1
    - (
        attendance_summary["absences"]
        / attendance_summary["attendance_events"]
    )
)

attendance_summary["attendance_rate"] *= 100


# ============================================================
# 2. LMS activity indicators
# ============================================================

lms_summary = (
    lms
    .groupby("student_id")
    .agg(
        total_logins=(
            "login_count",
            "sum",
        ),
        total_minutes=(
            "minutes_active",
            "sum",
        ),
        total_assignment_views=(
            "assignment_views",
            "sum",
        ),
        active_weeks=(
            "week_number",
            "nunique",
        ),
    )
    .reset_index()
)


# ------------------------------------------------------------
# LMS trend
# ------------------------------------------------------------

weekly_lms = (
    lms
    .groupby(
        [
            "student_id",
            "week_number",
        ]
    )
    .agg(
        weekly_minutes=(
            "minutes_active",
            "sum",
        ),
    )
    .reset_index()
)


early_lms = (
    weekly_lms[
        weekly_lms["week_number"] <= 3
    ]
    .groupby("student_id")["weekly_minutes"]
    .mean()
    .rename("early_lms_minutes")
)

recent_lms = (
    weekly_lms[
        weekly_lms["week_number"] >= 8
    ]
    .groupby("student_id")["weekly_minutes"]
    .mean()
    .rename("recent_lms_minutes")
)

lms_trend = pd.concat(
    [
        early_lms,
        recent_lms,
    ],
    axis=1,
).reset_index()

lms_trend["lms_change_pct"] = np.where(
    lms_trend["early_lms_minutes"] > 0,
    (
        (
            lms_trend["recent_lms_minutes"]
            - lms_trend["early_lms_minutes"]
        )
        / lms_trend["early_lms_minutes"]
    ) * 100,
    0,
)


# ============================================================
# 3. Assignment indicators
# ============================================================

assignments["submitted_numeric"] = pd.to_numeric(
    assignments["submitted"],
    errors="coerce",
)

assignment_summary = (
    assignments
    .groupby("student_id")
    .agg(
        assignment_count=(
            "submitted_numeric",
            "count",
        ),
        submissions=(
            "submitted_numeric",
            "sum",
        ),
    )
    .reset_index()
)

assignment_summary["submission_rate"] = (
    assignment_summary["submissions"]
    / assignment_summary["assignment_count"]
) * 100


# ============================================================
# 4. Assessment indicators
# ============================================================

assessment_summary = (
    assessments
    .groupby("student_id")
    .agg(
        assessment_count=(
            "score",
            "count",
        ),
        average_score=(
            "score",
            "mean",
        ),
    )
    .reset_index()
)


# ------------------------------------------------------------
# Assessment trend
# ------------------------------------------------------------

assessment_ordered = assessments.sort_values(
    [
        "student_id",
        "assessment_date",
    ]
).copy()

assessment_ordered["assessment_sequence"] = (
    assessment_ordered
    .groupby("student_id")
    .cumcount()
    + 1
)

early_scores = (
    assessment_ordered[
        assessment_ordered["assessment_sequence"] <= 2
    ]
    .groupby("student_id")["score"]
    .mean()
    .rename("early_score")
)

recent_scores = (
    assessment_ordered
    .groupby("student_id")
    .tail(2)
    .groupby("student_id")["score"]
    .mean()
    .rename("recent_score")
)

assessment_trend = pd.concat(
    [
        early_scores,
        recent_scores,
    ],
    axis=1,
).reset_index()

assessment_trend["score_change"] = (
    assessment_trend["recent_score"]
    - assessment_trend["early_score"]
)


# ============================================================
# 5. Combine student-level indicators
# ============================================================

risk_df = (
    students
    .merge(
        attendance_summary,
        on="student_id",
        how="left",
    )
    .merge(
        lms_summary,
        on="student_id",
        how="left",
    )
    .merge(
        lms_trend,
        on="student_id",
        how="left",
    )
    .merge(
        assignment_summary,
        on="student_id",
        how="left",
    )
    .merge(
        assessment_summary,
        on="student_id",
        how="left",
    )
    .merge(
        assessment_trend,
        on="student_id",
        how="left",
    )
)


# ============================================================
# Fill missing indicators
# ============================================================

numeric_columns = [
    "attendance_rate",
    "total_logins",
    "total_minutes",
    "total_assignment_views",
    "active_weeks",
    "early_lms_minutes",
    "recent_lms_minutes",
    "lms_change_pct",
    "assignment_count",
    "submissions",
    "submission_rate",
    "assessment_count",
    "average_score",
    "early_score",
    "recent_score",
    "score_change",
]

for column in numeric_columns:

    if column in risk_df.columns:

        risk_df[column] = pd.to_numeric(
            risk_df[column],
            errors="coerce",
        ).fillna(0)


# ============================================================
# 6. Calculate individual risk components
# ============================================================

# ------------------------------------------------------------
# Attendance risk: maximum 25 points
# ------------------------------------------------------------

def attendance_risk(rate: float) -> float:

    if rate >= 90:
        return 0

    if rate >= 80:
        return 10

    if rate >= 70:
        return 18

    return 25


risk_df["attendance_risk"] = (
    risk_df["attendance_rate"]
    .apply(attendance_risk)
)


# ------------------------------------------------------------
# LMS engagement risk: maximum 20 points
# ------------------------------------------------------------

def engagement_risk(
    active_weeks: float,
    change_pct: float,
) -> float:

    score = 0

    if active_weeks < 7:
        score += 8

    elif active_weeks < 9:
        score += 4

    if change_pct <= -50:
        score += 12

    elif change_pct <= -30:
        score += 9

    elif change_pct <= -15:
        score += 5

    return clamp(
        score,
        0,
        20,
    )


risk_df["engagement_risk"] = risk_df.apply(
    lambda row: engagement_risk(
        row["active_weeks"],
        row["lms_change_pct"],
    ),
    axis=1,
)


# ------------------------------------------------------------
# Assignment risk: maximum 20 points
# ------------------------------------------------------------

def assignment_risk(rate: float) -> float:

    if rate >= 90:
        return 0

    if rate >= 75:
        return 7

    if rate >= 60:
        return 14

    return 20


risk_df["assignment_risk"] = (
    risk_df["submission_rate"]
    .apply(assignment_risk)
)


# ------------------------------------------------------------
# Academic performance risk: maximum 25 points
# ------------------------------------------------------------

def performance_risk(score: float) -> float:

    if score >= 75:
        return 0

    if score >= 65:
        return 8

    if score >= 55:
        return 17

    return 25


risk_df["performance_risk"] = (
    risk_df["average_score"]
    .apply(performance_risk)
)


# ------------------------------------------------------------
# Performance trend risk: maximum 10 points
# ------------------------------------------------------------

def trend_risk(change: float) -> float:

    if change >= 0:
        return 0

    if change >= -5:
        return 3

    if change >= -10:
        return 6

    return 10


risk_df["trend_risk"] = (
    risk_df["score_change"]
    .apply(trend_risk)
)


# ============================================================
# 7. Total risk score
# ============================================================

risk_df["risk_score"] = (
    risk_df["attendance_risk"]
    + risk_df["engagement_risk"]
    + risk_df["assignment_risk"]
    + risk_df["performance_risk"]
    + risk_df["trend_risk"]
)

risk_df["risk_score"] = (
    risk_df["risk_score"]
    .clip(
        lower=0,
        upper=100,
    )
    .round(1)
)


risk_df["risk_band"] = (
    risk_df["risk_score"]
    .apply(risk_band)
)


# ============================================================
# 8. Explainable reason codes
# ============================================================

def identify_reasons(row: pd.Series) -> str:

    reasons = []

    if row["attendance_risk"] > 0:
        reasons.append(
            "Attendance"
        )

    if row["engagement_risk"] > 0:
        reasons.append(
            "LMS engagement"
        )

    if row["assignment_risk"] > 0:
        reasons.append(
            "Assignment submission"
        )

    if row["performance_risk"] > 0:
        reasons.append(
            "Assessment performance"
        )

    if row["trend_risk"] > 0:
        reasons.append(
            "Performance decline"
        )

    if not reasons:

        return "No material signal"

    return "; ".join(reasons)


risk_df["risk_reasons"] = risk_df.apply(
    identify_reasons,
    axis=1,
)


# ============================================================
# 9. Intervention priority
# ============================================================

def intervention_priority(
    band: str,
) -> str:

    mapping = {
        "Low": "Routine monitoring",
        "Moderate": "Review",
        "High": "Priority outreach",
        "Critical": "Urgent review",
    }

    return mapping.get(
        band,
        "Review",
    )


risk_df["intervention_priority"] = (
    risk_df["risk_band"]
    .apply(intervention_priority)
)


# ============================================================
# 10. Select public analytical columns
# ============================================================

output_columns = [
    "student_id",
    "programme_code",
    "programme",
    "school",
    "year_of_study",
    "enrolment_status",
    "attendance_rate",
    "active_weeks",
    "total_logins",
    "total_minutes",
    "lms_change_pct",
    "submission_rate",
    "average_score",
    "score_change",
    "attendance_risk",
    "engagement_risk",
    "assignment_risk",
    "performance_risk",
    "trend_risk",
    "risk_score",
    "risk_band",
    "risk_reasons",
    "intervention_priority",
]


risk_output = risk_df[
    output_columns
].copy()


# ============================================================
# 11. Summary by risk band
# ============================================================

risk_summary = (
    risk_output
    .groupby("risk_band")
    .agg(
        students=(
            "student_id",
            "count",
        ),
        average_score=(
            "average_score",
            "mean",
        ),
        average_attendance=(
            "attendance_rate",
            "mean",
        ),
        average_lms_change=(
            "lms_change_pct",
            "mean",
        ),
    )
    .reset_index()
)


risk_summary["percentage"] = (
    risk_summary["students"]
    / len(risk_output)
    * 100
)


# Force a logical risk-band ordering.
band_order = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Critical": 4,
}

risk_summary["_order"] = (
    risk_summary["risk_band"]
    .map(band_order)
)

risk_summary = (
    risk_summary
    .sort_values("_order")
    .drop(columns="_order")
)


# ============================================================
# 12. Programme-level summary
# ============================================================

programme_summary = (
    risk_output
    .groupby(
        [
            "school",
            "programme",
        ]
    )
    .agg(
        students=(
            "student_id",
            "count",
        ),
        average_risk_score=(
            "risk_score",
            "mean",
        ),
        high_or_critical=(
            "risk_band",
            lambda x: (
                x.isin(
                    [
                        "High",
                        "Critical",
                    ]
                )
                .sum()
            ),
        ),
        average_attendance=(
            "attendance_rate",
            "mean",
        ),
        average_score=(
            "average_score",
            "mean",
        ),
    )
    .reset_index()
)


programme_summary["high_or_critical_rate"] = (
    programme_summary["high_or_critical"]
    / programme_summary["students"]
    * 100
)


# ============================================================
# 13. Save outputs
# ============================================================

risk_output_path = (
    OUTPUT_DIR / "student_risk_scores.csv"
)

risk_summary_path = (
    OUTPUT_DIR / "risk_summary.csv"
)

programme_summary_path = (
    OUTPUT_DIR / "programme_risk_summary.csv"
)


risk_output.to_csv(
    risk_output_path,
    index=False,
)

risk_summary.to_csv(
    risk_summary_path,
    index=False,
)

programme_summary.to_csv(
    programme_summary_path,
    index=False,
)


# ============================================================
# 14. Console report
# ============================================================

print("\n")
print("=" * 72)
print("STUDENT SUCCESS ANALYTICS — EARLY WARNING MODEL")
print("=" * 72)

print(
    "\nModel type: Transparent rule-based scoring"
)

print(
    "Purpose: Demonstration only"
)

print(
    "\nRisk score components:"
)

print(
    "  Attendance              0–25 points"
)

print(
    "  LMS engagement          0–20 points"
)

print(
    "  Assignment submission   0–20 points"
)

print(
    "  Academic performance    0–25 points"
)

print(
    "  Performance trend       0–10 points"
)

print("\n" + "-" * 72)
print("RISK DISTRIBUTION")
print("-" * 72)

print(
    risk_summary.to_string(
        index=False,
        formatters={
            "percentage": "{:.1f}%".format,
            "average_score": "{:.1f}".format,
            "average_attendance": "{:.1f}".format,
            "average_lms_change": "{:.1f}%".format,
        },
    )
)


print("\n" + "-" * 72)
print("TOP 20 STUDENTS BY RISK SCORE")
print("-" * 72)

top_risk = (
    risk_output
    .sort_values(
        "risk_score",
        ascending=False,
    )
    .head(20)
)

print(
    top_risk[
        [
            "student_id",
            "programme",
            "risk_score",
            "risk_band",
            "risk_reasons",
        ]
    ].to_string(
        index=False
    )
)


print("\n" + "-" * 72)
print("PROGRAMME SUMMARY")
print("-" * 72)

print(
    programme_summary
    .sort_values(
        "average_risk_score",
        ascending=False,
    )
    .head(12)
    .to_string(
        index=False,
        formatters={
            "average_risk_score": "{:.1f}".format,
            "high_or_critical_rate": "{:.1f}%".format,
            "average_attendance": "{:.1f}".format,
            "average_score": "{:.1f}".format,
        },
    )
)


print("\n" + "-" * 72)
print("OUTPUT FILES")
print("-" * 72)

print(
    f"Student scores:       {risk_output_path}"
)

print(
    f"Risk summary:         {risk_summary_path}"
)

print(
    f"Programme summary:    {programme_summary_path}"
)

print("\nEarly-warning analysis complete.")
print("=" * 72)