"""
Synthetic survey and feedback analytics.

All results are descriptive summaries of synthetic data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "surveys"
    / "survey_responses.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "survey_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Load
# ============================================================

if not INPUT_PATH.exists():

    raise FileNotFoundError(
        f"Survey data not found: {INPUT_PATH}"
    )


df = pd.read_csv(
    INPUT_PATH
)


df["survey_date"] = pd.to_datetime(
    df["survey_date"],
    errors="coerce",
)


df["score"] = pd.to_numeric(
    df["score"],
    errors="coerce",
)


# ============================================================
# Overall summary
# ============================================================

responded = df[
    df["score"].notna()
].copy()


total_records = len(df)

response_records = len(
    responded
)


response_rate = (
    response_records
    / total_records
    * 100
    if total_records
    else 0
)


average_score = (
    responded["score"].mean()
    if not responded.empty
    else 0
)


recommendation_rate = (
    responded["would_recommend"].mean()
    * 100
    if not responded.empty
    else 0
)


overall_summary = pd.DataFrame(
    [
        {
            "metric":
                "Survey records",
            "value":
                total_records,
        },
        {
            "metric":
                "Responses with score",
            "value":
                response_records,
        },
        {
            "metric":
                "Response rate",
            "value":
                response_rate,
        },
        {
            "metric":
                "Average satisfaction score",
            "value":
                average_score,
        },
        {
            "metric":
                "Would recommend rate",
            "value":
                recommendation_rate,
        },
    ]
)


# ============================================================
# Respondent type
# ============================================================

respondent_summary = (
    responded
    .groupby(
        "respondent_type"
    )
    .agg(
        responses=(
            "response_id",
            "count",
        ),
        average_score=(
            "score",
            "mean",
        ),
        recommendation_rate=(
            "would_recommend",
            "mean",
        ),
    )
    .reset_index()
)


respondent_summary[
    "recommendation_rate"
] *= 100


# ============================================================
# Theme analysis
# ============================================================

theme_summary = (
    responded
    .groupby(
        [
            "respondent_type",
            "theme",
        ]
    )
    .agg(
        responses=(
            "response_id",
            "count",
        ),
        average_score=(
            "score",
            "mean",
        ),
    )
    .reset_index()
)


# ============================================================
# Monthly / date trend
# ============================================================

trend_summary = (
    responded
    .assign(
        survey_week=lambda x:
            x["survey_date"].dt.to_period(
                "W"
            ).astype(str)
    )
    .groupby(
        [
            "survey_week",
            "respondent_type",
        ]
    )
    .agg(
        responses=(
            "response_id",
            "count",
        ),
        average_score=(
            "score",
            "mean",
        ),
    )
    .reset_index()
)


# ============================================================
# Save
# ============================================================

outputs = {
    "survey_summary.csv":
        overall_summary,

    "survey_respondent_summary.csv":
        respondent_summary,

    "survey_theme_summary.csv":
        theme_summary,

    "survey_trend.csv":
        trend_summary,
}


print()
print("=" * 72)
print(
    "STUDENT SUCCESS ANALYTICS — SURVEY ANALYSIS"
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
        f"✓ {filename:<36}"
        f"{len(output):>8,} rows"
    )


print()
print("-" * 72)
print("SUMMARY")
print("-" * 72)

print(
    f"Survey records:       {total_records:,}"
)

print(
    f"Scored responses:     {response_records:,}"
)

print(
    f"Response rate:        {response_rate:.1f}%"
)

print(
    f"Average score:        {average_score:.2f} / 5"
)

print(
    f"Recommendation rate:  {recommendation_rate:.1f}%"
)

print()
print(
    "All survey results are synthetic and descriptive."
)

print("=" * 72)
