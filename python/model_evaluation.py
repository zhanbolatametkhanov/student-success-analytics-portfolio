"""
Student Success Analytics
Early-Warning Model Evaluation

Purpose
-------
Evaluate the transparent risk model against the synthetic
simulation reference.

IMPORTANT
---------
simulation_truth.csv is used ONLY for evaluation.

It is NOT used as an input feature when calculating
student risk scores.

This is a portfolio demonstration using synthetic data only.
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


# ============================================================
# Load data
# ============================================================

risk_df = pd.read_csv(
    RISK_FILE
)

truth_df = pd.read_csv(
    TRUTH_FILE
)


# ============================================================
# Merge model output and reference
# ============================================================

evaluation_df = risk_df[
    [
        "student_id",
        "risk_score",
        "risk_band",
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
# Integrity checks
# ============================================================

if len(evaluation_df) != len(risk_df):

    raise ValueError(
        "Not every model record has a matching "
        "simulation reference record."
    )

if len(evaluation_df) != len(truth_df):

    raise ValueError(
        "Not every simulation reference record has "
        "a matching model record."
    )


if evaluation_df["student_id"].duplicated().any():

    raise ValueError(
        "Duplicate student IDs detected after merge."
    )


print("\n")
print("=" * 72)
print("STUDENT SUCCESS ANALYTICS — MODEL EVALUATION")
print("=" * 72)

print(
    f"\nStudents evaluated: {len(evaluation_df):,}"
)

print(
    "\nIMPORTANT:"
)

print(
    "simulation_truth.csv is evaluation-only and was "
    "not used to generate the model score."
)


# ============================================================
# Binary classification definition
# ============================================================

HIGH_NEED = {
    "High",
    "Critical",
}

MODEL_POSITIVE_BANDS = {
    "High",
    "Critical",
}


evaluation_df["actual_positive"] = (
    evaluation_df[
        "simulated_support_need"
    ]
    .isin(HIGH_NEED)
)

evaluation_df["predicted_positive"] = (
    evaluation_df[
        "risk_band"
    ]
    .isin(MODEL_POSITIVE_BANDS)
)


# ============================================================
# Confusion matrix
# ============================================================

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


# ============================================================
# Metrics
# ============================================================

total = len(evaluation_df)

accuracy = (
    (true_positive + true_negative)
    / total
    if total
    else 0
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


# ============================================================
# Population rates
# ============================================================

actual_positive_rate = (
    evaluation_df["actual_positive"].mean()
)

predicted_positive_rate = (
    evaluation_df["predicted_positive"].mean()
)


# ============================================================
# Exact four-band agreement
# ============================================================

band_order = [
    "Low",
    "Moderate",
    "High",
    "Critical",
]

evaluation_df["simulated_support_need"] = (
    pd.Categorical(
        evaluation_df[
            "simulated_support_need"
        ],
        categories=band_order,
        ordered=True,
    )
)

evaluation_df["risk_band"] = (
    pd.Categorical(
        evaluation_df["risk_band"],
        categories=band_order,
        ordered=True,
    )
)


exact_band_match = (
    evaluation_df[
        "risk_band"
    ]
    == evaluation_df[
        "simulated_support_need"
    ]
).mean()


# ============================================================
# Confusion matrix dataframe
# ============================================================

confusion_matrix = pd.DataFrame(
    [
        {
            "actual": "High/Critical",
            "predicted": "High/Critical",
            "count": true_positive,
        },
        {
            "actual": "High/Critical",
            "predicted": "Low/Moderate",
            "count": false_negative,
        },
        {
            "actual": "Low/Moderate",
            "predicted": "High/Critical",
            "count": false_positive,
        },
        {
            "actual": "Low/Moderate",
            "predicted": "Low/Moderate",
            "count": true_negative,
        },
    ]
)


# ============================================================
# Metric table
# ============================================================

metrics_df = pd.DataFrame(
    [
        {
            "metric": "Accuracy",
            "value": accuracy,
            "definition":
                "Proportion of all classifications that were correct",
        },
        {
            "metric": "Precision",
            "value": precision,
            "definition":
                "Proportion of predicted High/Critical cases "
                "that were High/Critical in the simulation reference",
        },
        {
            "metric": "Recall",
            "value": recall,
            "definition":
                "Proportion of simulated High/Critical cases "
                "identified by the model",
        },
        {
            "metric": "Specificity",
            "value": specificity,
            "definition":
                "Proportion of simulated Low/Moderate cases "
                "correctly left below the High/Critical threshold",
        },
        {
            "metric": "F1",
            "value": f1,
            "definition":
                "Harmonic mean of precision and recall",
        },
        {
            "metric": "Exact four-band agreement",
            "value": exact_band_match,
            "definition":
                "Proportion where model band exactly matched "
                "the simulated reference band",
        },
    ]
)


# ============================================================
# Risk-band comparison
# ============================================================

band_comparison = (
    evaluation_df
    .groupby(
        [
            "simulated_support_need",
            "risk_band",
        ],
        observed=False,
    )
    .size()
    .reset_index(
        name="students"
    )
)


# ============================================================
# Error analysis
# ============================================================

error_df = evaluation_df[
    evaluation_df["actual_positive"]
    !=
    evaluation_df["predicted_positive"]
].copy()

error_df["error_type"] = (
    error_df.apply(
        lambda row:
            (
                "False Positive"
                if row["predicted_positive"]
                else "False Negative"
            ),
        axis=1,
    )
)


# ============================================================
# Save outputs
# ============================================================

confusion_path = (
    OUTPUT_DIR
    / "model_confusion_matrix.csv"
)

metrics_path = (
    OUTPUT_DIR
    / "model_metrics.csv"
)

band_path = (
    OUTPUT_DIR
    / "model_band_comparison.csv"
)

errors_path = (
    OUTPUT_DIR
    / "model_errors.csv"
)

evaluated_path = (
    OUTPUT_DIR
    / "evaluated_student_risk.csv"
)


confusion_matrix.to_csv(
    confusion_path,
    index=False,
)

metrics_df.to_csv(
    metrics_path,
    index=False,
)

band_comparison.to_csv(
    band_path,
    index=False,
)

error_df[
    [
        "student_id",
        "risk_score",
        "risk_band",
        "simulated_support_need",
        "error_type",
    ]
].to_csv(
    errors_path,
    index=False,
)

evaluation_df.to_csv(
    evaluated_path,
    index=False,
)


# ============================================================
# Console output
# ============================================================

print("\n")
print("-" * 72)
print("BINARY CLASSIFICATION DEFINITION")
print("-" * 72)

print(
    "Positive = High or Critical"
)

print(
    "Negative = Low or Moderate"
)


print("\n")
print("-" * 72)
print("CONFUSION MATRIX")
print("-" * 72)

print(
    f"True Positive:   {true_positive:>5,}"
)

print(
    f"False Positive:  {false_positive:>5,}"
)

print(
    f"True Negative:   {true_negative:>5,}"
)

print(
    f"False Negative:  {false_negative:>5,}"
)


print("\n")
print("-" * 72)
print("MODEL METRICS")
print("-" * 72)

print(
    f"Accuracy:                 {accuracy:.3f}"
)

print(
    f"Precision:                {precision:.3f}"
)

print(
    f"Recall:                   {recall:.3f}"
)

print(
    f"Specificity:              {specificity:.3f}"
)

print(
    f"F1:                       {f1:.3f}"
)

print(
    f"Exact four-band agreement:{exact_band_match:.3f}"
)


print("\n")
print("-" * 72)
print("POPULATION RATES")
print("-" * 72)

print(
    f"Actual High/Critical:     "
    f"{actual_positive_rate * 100:.1f}%"
)

print(
    f"Predicted High/Critical:  "
    f"{predicted_positive_rate * 100:.1f}%"
)


print("\n")
print("-" * 72)
print("ERROR ANALYSIS")
print("-" * 72)

print(
    f"Total classification errors: {len(error_df):,}"
)

false_negative_count = int(
    (
        error_df["error_type"]
        == "False Negative"
    ).sum()
)

false_positive_count = int(
    (
        error_df["error_type"]
        == "False Positive"
    ).sum()
)

print(
    f"False negatives:              {false_negative_count:,}"
)

print(
    f"False positives:              {false_positive_count:,}"
)


print("\n")
print("-" * 72)
print("OUTPUT FILES")
print("-" * 72)

print(
    f"Metrics:            {metrics_path}"
)

print(
    f"Confusion matrix:   {confusion_path}"
)

print(
    f"Band comparison:    {band_path}"
)

print(
    f"Errors:             {errors_path}"
)

print(
    f"Evaluated records:  {evaluated_path}"
)


print("\n")
print("=" * 72)
print("MODEL EVALUATION COMPLETE")
print("=" * 72)