"""
Synthetic Student & Faculty Feedback Generator.

Creates portfolio-only survey records demonstrating:
- student feedback
- faculty feedback
- satisfaction measures
- thematic categories

All records are synthetic.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "surveys"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


RNG = np.random.default_rng(
    20260928
)


# ============================================================
# Configuration
# ============================================================

STUDENT_COUNT = 2500

STUDENT_RESPONSE_COUNT = 1500

FACULTY_RESPONSE_COUNT = 250


STUDENT_THEMES = [
    "Advising access",
    "Tutoring usefulness",
    "Study skills",
    "Communication",
    "Scheduling",
    "Academic resources",
]


FACULTY_THEMES = [
    "Referral process",
    "Data visibility",
    "Communication",
    "Intervention coordination",
    "Dashboard usefulness",
]


# ============================================================
# Student survey
# ============================================================

student_rows = []

for i in range(
    STUDENT_RESPONSE_COUNT
):

    student_number = int(
        RNG.integers(
            1,
            STUDENT_COUNT + 1,
        )
    )

    student_id = (
        f"STU{student_number:06d}"
    )

    survey_date = (
        pd.Timestamp("2026-09-01")
        + pd.Timedelta(
            days=int(
                RNG.integers(
                    0,
                    28,
                )
            )
        )
    )

    theme = RNG.choice(
        STUDENT_THEMES
    )

    score = int(
        RNG.integers(
            1,
            6,
        )
    )

    responded = int(
        RNG.random()
        < 0.93
    )

    student_rows.append(
        {
            "response_id":
                f"STU-FB-{i + 1:05d}",

            "respondent_type":
                "Student",

            "student_id":
                student_id,

            "survey_date":
                survey_date.date().isoformat(),

            "theme":
                theme,

            "question":
                "How useful was the support experience?",

            "score":
                score
                if responded
                else np.nan,

            "would_recommend":
                int(
                    RNG.random() < 0.70
                )
                if responded
                else np.nan,
        }
    )


student_df = pd.DataFrame(
    student_rows
)


# ============================================================
# Faculty survey
# ============================================================

faculty_rows = []

for i in range(
    FACULTY_RESPONSE_COUNT
):

    survey_date = (
        pd.Timestamp("2026-09-01")
        + pd.Timedelta(
            days=int(
                RNG.integers(
                    0,
                    28,
                )
            )
        )
    )

    theme = RNG.choice(
        FACULTY_THEMES
    )

    score = int(
        RNG.integers(
            1,
            6,
        )
    )

    responded = int(
        RNG.random()
        < 0.95
    )

    faculty_rows.append(
        {
            "response_id":
                f"FAC-FB-{i + 1:05d}",

            "respondent_type":
                "Faculty",

            "student_id":
                np.nan,

            "survey_date":
                survey_date.date().isoformat(),

            "theme":
                theme,

            "question":
                "How useful was the support coordination process?",

            "score":
                score
                if responded
                else np.nan,

            "would_recommend":
                int(
                    RNG.random() < 0.75
                )
                if responded
                else np.nan,
        }
    )


faculty_df = pd.DataFrame(
    faculty_rows
)


# ============================================================
# Combine
# ============================================================

survey_df = pd.concat(
    [
        student_df,
        faculty_df,
    ],
    ignore_index=True,
)


# ============================================================
# Save
# ============================================================

output_path = (
    DATA_DIR
    / "survey_responses.csv"
)


survey_df.to_csv(
    output_path,
    index=False,
)


print()
print("=" * 72)
print(
    "STUDENT SUCCESS ANALYTICS — SURVEY DATA GENERATOR"
)
print("=" * 72)

print(
    f"\nTotal survey records: "
    f"{len(survey_df):,}"
)

print(
    f"Student records:       "
    f"{len(student_df):,}"
)

print(
    f"Faculty records:       "
    f"{len(faculty_df):,}"
)

print(
    f"\n✓ {output_path}"
)

print()
print(
    "All survey responses are synthetic."
)

print("=" * 72)
