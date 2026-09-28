"""
Student Success Analytics
Early-Warning Threshold Analysis

Purpose
-------
Examine how different operational risk thresholds affect:

- number of students flagged
- precision
- recall
- specificity
- false positives
- false negatives

This is a synthetic demonstration only.

Important
---------
The simulation reference is used only for evaluation.
It is never used to calculate the original risk score.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path("data/synthetic")

RISK_FILE = (
    DATA_DIR
    / "risk_reports"
    / "student_risk_scores.csv"
)

TRUTH_FILE = (
    DATA_DIR
    / "simulation_truth.csv"
)

OUTPUT_DIR = (
    DATA_DIR
    / "risk_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


THRESHOLDS = [
    20,
    30,
    40,
    50,
    60,
    70,
    80,
]


# ============================================================
# Load data
# ============================================================

risk_df = pd.read_csv(
    RISK_FILE
)

truth_df = pd.read_csv(
    TRUTH_FILE
)


evaluation_df = risk_df[
    [
        "student_id",
        "risk_score",
    ]
].merge(
    truth_df[
        [
            "student_id",
            "simulated_support_need",
        ]
    ],
    on="student_id",
    how="inner",
)


# ============================================================
# Define simulated positive population
# ============================================================

evaluation_df["actual_positive"] = (
    evaluation_df[
        "simulated_support_need"
    ].isin(
        [
            "High",
            "Critical",
        ]
    )
)


# ============================================================
# Calculate metrics at each threshold
# ============================================================

rows = []


for threshold in THRESHOLDS:

    evaluation_df["predicted_positive"] = (
        evaluation_df["risk_score"]
        >= threshold
    )


    true_positive = int(
        (
            evaluation_df["actual_positive"]
            & evaluation_df["predicted_positive"]
        ).sum()
    )


    false_positive = int(
        (
            ~evaluation_df["actual_positive"]
            & evaluation_df["predicted_positive"]
        ).sum()
    )


    true_negative = int(
        (
            ~evaluation_df["actual_positive"]
            & ~evaluation_df["predicted_positive"]
        ).sum()
    )


    false_negative = int(
        (
            evaluation_df["actual_positive"]
            & ~evaluation_df["predicted_positive"]
        ).sum()
    )


    flagged_students = int(
        evaluation_df[
            "predicted_positive"
        ].sum()
    )


    total_students = len(
        evaluation_df
    )


    precision = (
        true_positive
        / (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0
    )


    recall = (
        true_positive
        / (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0
    )


    specificity = (
        true_negative
        / (true_negative + false_positive)
        if (true_negative + false_positive)
        else 0
    )


    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0
    )


    flagged_rate = (
        flagged_students
        / total_students
        if total_students
        else 0
    )


    rows.append(
        {
            "threshold": threshold,
            "flagged_students": flagged_students,
            "flagged_rate": flagged_rate,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "specificity": specificity,
            "f1": f1,
        }
    )


threshold_df = pd.DataFrame(
    rows
)


# ============================================================
# Save result
# ============================================================

output_path = (
    OUTPUT_DIR
    / "threshold_analysis.csv"
)

threshold_df.to_csv(
    output_path,
    index=False,
)


# ============================================================
# Console report
# ============================================================

print("\n")
print("=" * 88)
print("STUDENT SUCCESS ANALYTICS — RISK THRESHOLD ANALYSIS")
print("=" * 88)

print(
    "\nPositive reference population = High or Critical"
)

print(
    "\nNo threshold is treated as inherently correct. "
    "The purpose is to expose the operational trade-off."
)


print("\n")
print("-" * 88)
print("THRESHOLD COMPARISON")
print("-" * 88)


display_df = threshold_df.copy()


for column in [
    "flagged_rate",
    "precision",
    "recall",
    "specificity",
    "f1",
]:

    display_df[column] = (
        display_df[column] * 100
    ).round(1)


print(
    display_df.to_string(
        index=False
    )
)


print("\n")
print("-" * 88)
print("INTERPRETATION")
print("-" * 88)

print(
    "Lower thresholds generally increase the number of students "
    "flagged and can improve recall, while increasing the workload "
    "and potentially increasing false positives."
)

print(
    "Higher thresholds generally reduce the number of students "
    "flagged and can improve precision, while potentially missing "
    "more students in the simulated positive population."
)

print(
    "\nThese relationships are specific to the synthetic dataset "
    "and should not be interpreted as empirical university evidence."
)


print("\n")
print("-" * 88)
print("OUTPUT")
print("-" * 88)

print(
    f"Threshold analysis: {output_path}"
)


print("\n")
print("=" * 88)
print("THRESHOLD ANALYSIS COMPLETE")
print("=" * 88)