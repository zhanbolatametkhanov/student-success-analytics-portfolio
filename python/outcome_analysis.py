
"""
Student Success Analytics
Intervention Outcome & Effectiveness Analysis

All data is synthetic.
Cost figures are illustrative portfolio assumptions only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
)

OUTPUT_DIR = (
    DATA_DIR
    / "outcome_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


INTERVENTION_FILE = (
    DATA_DIR
    / "interventions.csv"
)


COST_ASSUMPTIONS = {
    "Academic advising": 45.0,
    "Tutoring referral": 65.0,
    "Faculty outreach": 35.0,
    "Study skills support": 50.0,
}


POSITIVE_OUTCOMES = {
    "Student engaged",
    "Support provided",
}


def classify_outcome(
    outcome: str,
) -> str:

    if outcome in POSITIVE_OUTCOMES:
        return "Positive"

    if outcome in {
        "No response",
        "Monitoring continued",
        "Not yet assessed",
    }:
        return "Unresolved"

    return "Other"


# ============================================================
# Load
# ============================================================

if not INTERVENTION_FILE.exists():

    raise FileNotFoundError(
        f"Intervention file not found: {INTERVENTION_FILE}"
    )


df = pd.read_csv(
    INTERVENTION_FILE
)


required_columns = {
    "intervention_id",
    "student_id",
    "risk_type",
    "trigger_date",
    "intervention_type",
    "advisor",
    "status",
    "outcome",
}


missing = (
    required_columns
    - set(df.columns)
)


if missing:

    raise ValueError(
        "Missing required columns: "
        + ", ".join(sorted(missing))
    )


# ============================================================
# Derived fields
# ============================================================

df["estimated_cost"] = (
    df["intervention_type"]
    .map(COST_ASSUMPTIONS)
)


df["outcome_category"] = (
    df["outcome"]
    .astype(str)
    .apply(classify_outcome)
)


df["completed_flag"] = (
    df["status"]
    == "Completed"
).astype(int)


df["positive_outcome_flag"] = (
    df["outcome_category"]
    == "Positive"
).astype(int)


df["outcome_assessed_flag"] = (
    ~df["outcome"].isin(
        [
            "Not yet assessed",
            "",
        ]
    )
).astype(int)


# ============================================================
# Overall metrics
# ============================================================

total_interventions = len(df)

completed_interventions = int(
    df["completed_flag"].sum()
)

assessed_interventions = int(
    df["outcome_assessed_flag"].sum()
)

positive_outcomes = int(
    df["positive_outcome_flag"].sum()
)

estimated_total_cost = float(
    df["estimated_cost"]
    .fillna(0)
    .sum()
)


completion_rate = (
    completed_interventions
    / total_interventions
    * 100
    if total_interventions
    else 0
)


positive_rate_all = (
    positive_outcomes
    / total_interventions
    * 100
    if total_interventions
    else 0
)


positive_rate_assessed = (
    positive_outcomes
    / assessed_interventions
    * 100
    if assessed_interventions
    else 0
)


cost_per_completed = (
    estimated_total_cost
    / completed_interventions
    if completed_interventions
    else 0
)


cost_per_positive_outcome = (
    estimated_total_cost
    / positive_outcomes
    if positive_outcomes
    else 0
)


# ============================================================
# Intervention type summary
# ============================================================

type_summary = (
    df
    .groupby("intervention_type")
    .agg(
        interventions=(
            "intervention_id",
            "count",
        ),
        completed=(
            "completed_flag",
            "sum",
        ),
        assessed=(
            "outcome_assessed_flag",
            "sum",
        ),
        positive_outcomes=(
            "positive_outcome_flag",
            "sum",
        ),
        estimated_cost=(
            "estimated_cost",
            "sum",
        ),
    )
    .reset_index()
)


type_summary["completion_rate"] = (
    type_summary["completed"]
    / type_summary["interventions"]
    * 100
)


type_summary["positive_outcome_rate_all"] = (
    type_summary["positive_outcomes"]
    / type_summary["interventions"]
    * 100
)


type_summary["positive_outcome_rate_assessed"] = (
    type_summary["positive_outcomes"]
    / type_summary["assessed"]
    * 100
).fillna(0)


type_summary["cost_per_completed"] = (
    type_summary["estimated_cost"]
    / type_summary["completed"]
).replace(
    [float("inf")],
    0,
).fillna(0)


type_summary["cost_per_positive_outcome"] = (
    type_summary["estimated_cost"]
    / type_summary["positive_outcomes"]
).replace(
    [float("inf")],
    0,
).fillna(0)


# ============================================================
# Risk type summary
# ============================================================

risk_type_summary = (
    df
    .groupby("risk_type")
    .agg(
        interventions=(
            "intervention_id",
            "count",
        ),
        completed=(
            "completed_flag",
            "sum",
        ),
        positive_outcomes=(
            "positive_outcome_flag",
            "sum",
        ),
    )
    .reset_index()
)


risk_type_summary["completion_rate"] = (
    risk_type_summary["completed"]
    / risk_type_summary["interventions"]
    * 100
)


risk_type_summary["positive_outcome_rate"] = (
    risk_type_summary["positive_outcomes"]
    / risk_type_summary["interventions"]
    * 100
)


# ============================================================
# Outcome distribution
# ============================================================

outcome_distribution = (
    df
    .groupby(
        [
            "outcome_category",
            "outcome",
        ]
    )
    .size()
    .reset_index(
        name="interventions"
    )
)


# ============================================================
# Status funnel
# ============================================================

status_funnel = (
    df
    .groupby("status")
    .size()
    .reindex(
        [
            "Pending",
            "In progress",
            "Completed",
        ],
        fill_value=0,
    )
    .reset_index(
        name="interventions"
    )
)


# ============================================================
# Advisor workload
# ============================================================

advisor_summary = (
    df
    .groupby("advisor")
    .agg(
        assigned_cases=(
            "intervention_id",
            "count",
        ),
        completed_cases=(
            "completed_flag",
            "sum",
        ),
        positive_outcomes=(
            "positive_outcome_flag",
            "sum",
        ),
    )
    .reset_index()
)


advisor_summary["completion_rate"] = (
    advisor_summary["completed_cases"]
    / advisor_summary["assigned_cases"]
    * 100
)


# ============================================================
# Summary metrics
# ============================================================

summary_metrics = pd.DataFrame(
    [
        {
            "metric":
                "Total interventions",
            "value":
                total_interventions,
            "unit":
                "cases",
        },
        {
            "metric":
                "Completed interventions",
            "value":
                completed_interventions,
            "unit":
                "cases",
        },
        {
            "metric":
                "Completion rate",
            "value":
                completion_rate,
            "unit":
                "percent",
        },
        {
            "metric":
                "Outcome-assessed interventions",
            "value":
                assessed_interventions,
            "unit":
                "cases",
        },
        {
            "metric":
                "Positive synthetic outcomes",
            "value":
                positive_outcomes,
            "unit":
                "cases",
        },
        {
            "metric":
                "Positive outcome rate — all interventions",
            "value":
                positive_rate_all,
            "unit":
                "percent",
        },
        {
            "metric":
                "Positive outcome rate — assessed cases",
            "value":
                positive_rate_assessed,
            "unit":
                "percent",
        },
        {
            "metric":
                "Estimated intervention cost",
            "value":
                estimated_total_cost,
            "unit":
                "synthetic cost units",
        },
        {
            "metric":
                "Estimated cost per completed intervention",
            "value":
                cost_per_completed,
            "unit":
                "synthetic cost units",
        },
        {
            "metric":
                "Estimated cost per positive outcome",
            "value":
                cost_per_positive_outcome,
            "unit":
                "synthetic cost units",
        },
    ]
)


# ============================================================
# Illustrative cost assumptions
# ============================================================

cost_table = pd.DataFrame(
    [
        {
            "intervention_type":
                intervention_type,
            "illustrative_cost":
                cost,
            "note":
                "Synthetic portfolio assumption only",
        }
        for intervention_type, cost
        in COST_ASSUMPTIONS.items()
    ]
)


# ============================================================
# Write files
# ============================================================

outputs = {
    "outcome_summary_metrics.csv":
        summary_metrics,

    "intervention_type_summary.csv":
        type_summary,

    "risk_type_outcome_summary.csv":
        risk_type_summary,

    "outcome_distribution.csv":
        outcome_distribution,

    "intervention_status_funnel.csv":
        status_funnel,

    "advisor_workload_summary.csv":
        advisor_summary,

    "illustrative_cost_assumptions.csv":
        cost_table,
}


print()
print("=" * 72)
print(
    "STUDENT SUCCESS ANALYTICS — OUTCOME ANALYSIS"
)
print("=" * 72)


for filename, output in outputs.items():

    path = (
        OUTPUT_DIR
        / filename
    )

    output.to_csv(
        path,
        index=False,
    )

    print(
        f"✓ {filename:<42}"
        f"{len(output):>8,} rows"
    )


print()
print("-" * 72)
print("SUMMARY")
print("-" * 72)

print(
    f"Total interventions:       {total_interventions:,}"
)

print(
    f"Completed:                  {completed_interventions:,}"
)

print(
    f"Completion rate:            {completion_rate:.1f}%"
)

print(
    f"Positive outcomes:          {positive_outcomes:,}"
)

print(
    f"Positive outcome rate:      {positive_rate_all:.1f}%"
)

print(
    f"Estimated synthetic cost:   {estimated_total_cost:.2f}"
)

print()
print(
    "All outcome and cost figures are synthetic demonstration values."
)
print("=" * 72)
