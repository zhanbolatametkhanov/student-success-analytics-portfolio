"""
Synthetic Student Success Analytics Dataset Generator

Purpose
-------
Generate a reproducible, internally consistent fictional university
dataset suitable for demonstrating:

- SIS data
- LMS activity
- attendance
- assignments
- assessments
- intervention workflows
- data-quality monitoring
- early-warning analytics

Important
---------
This project uses synthetic data only.
No real student, staff, university, or institutional records are used.

The simulation contains an internal "support need" signal only so that
later we can evaluate whether our transparent risk rules identify the
patterns we intentionally created. The risk model itself will NOT use
that field.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

RANDOM_SEED = 20260928
NUMBER_OF_STUDENTS = 2500
WEEKS = 10

OUTPUT_DIR = Path("data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(RANDOM_SEED)

SEMESTER = "Fall 2026"
START_DATE = datetime(2026, 9, 1)


# ============================================================
# Reference data
# ============================================================

PROGRAMMES = [
    (
        "CS",
        "Computer Science",
        "School of Engineering and Digital Sciences",
    ),
    (
        "AI",
        "Artificial Intelligence",
        "School of Engineering and Digital Sciences",
    ),
    (
        "EE",
        "Electrical Engineering",
        "School of Engineering and Digital Sciences",
    ),
    (
        "ME",
        "Mechanical Engineering",
        "School of Engineering and Digital Sciences",
    ),
    (
        "CE",
        "Civil Engineering",
        "School of Mining and Geosciences",
    ),
    (
        "ECON",
        "Economics",
        "Graduate School of Business",
    ),
    (
        "FIN",
        "Finance",
        "Graduate School of Business",
    ),
    (
        "PSIR",
        "Political Science and International Relations",
        "School of Sciences and Humanities",
    ),
    (
        "SOCI",
        "Sociology",
        "School of Sciences and Humanities",
    ),
    (
        "CHEM",
        "Chemistry",
        "School of Sciences and Humanities",
    ),
    (
        "BIO",
        "Biological Sciences",
        "School of Sciences and Humanities",
    ),
    (
        "PHYS",
        "Physics",
        "School of Sciences and Humanities",
    ),
]


COURSES = [
    ("CS101", "Introduction to Programming", 5, "CS"),
    ("CS201", "Data Structures", 5, "CS"),
    ("CS301", "Database Systems", 5, "CS"),
    ("AI201", "Machine Learning Foundations", 5, "AI"),
    ("AI301", "Applied Artificial Intelligence", 5, "AI"),
    ("EE201", "Digital Systems", 5, "EE"),
    ("EE301", "Signals and Systems", 5, "EE"),
    ("ME201", "Engineering Mechanics", 5, "ME"),
    ("CE201", "Structural Engineering", 5, "CE"),
    ("ECON201", "Microeconomics", 5, "ECON"),
    ("ECON301", "Econometrics", 5, "ECON"),
    ("FIN201", "Corporate Finance", 5, "FIN"),
    ("PSIR201", "Comparative Politics", 5, "PSIR"),
    ("SOCI201", "Social Research Methods", 5, "SOCI"),
    ("CHEM201", "Organic Chemistry", 5, "CHEM"),
    ("BIO201", "Molecular Biology", 5, "BIO"),
    ("PHYS201", "Classical Mechanics", 5, "PHYS"),
    ("MATH201", "Applied Mathematics", 5, "MATH"),
]


ASSESSMENT_TYPES = [
    "Quiz",
    "Midterm",
    "Assignment",
]


INTERVENTION_TYPES = [
    "Academic advising",
    "Tutoring referral",
    "Faculty outreach",
    "Study skills support",
]


RISK_TYPES = [
    "Attendance",
    "Academic performance",
    "LMS engagement",
    "Multiple indicators",
]


INTERVENTION_OUTCOMES = [
    "Student engaged",
    "Support provided",
    "No response",
    "Monitoring continued",
]


# ============================================================
# Helper functions
# ============================================================

def clip(value: float, minimum: float, maximum: float) -> float:
    """Keep a numeric value inside a specified range."""
    return float(np.clip(value, minimum, maximum))


def sigmoid(x: float) -> float:
    """Simple logistic transformation."""
    return 1.0 / (1.0 + np.exp(-x))


def date_for_week(week_number: int) -> datetime:
    """Return the Monday-ish reference date for a simulation week."""
    return START_DATE + timedelta(days=(week_number - 1) * 7)


# ============================================================
# 1. Students
# ============================================================

students = []

for i in range(1, NUMBER_OF_STUDENTS + 1):

    programme_code, programme_name, school = PROGRAMMES[
        int(rng.integers(0, len(PROGRAMMES)))
    ]

    year = int(rng.integers(1, 5))

    # Simulated latent characteristics.
    # These are only used to generate coherent synthetic behaviour.
    baseline_engagement = clip(
        rng.normal(0.65, 0.18),
        0.10,
        0.98,
    )

    academic_preparedness = clip(
        rng.normal(0.68, 0.15),
        0.15,
        0.98,
    )

    # A small synthetic population is intentionally generated with
    # elevated support needs. This is not a real-world estimate.
    support_need_signal = (
        0.45 * (1 - baseline_engagement)
        + 0.35 * (1 - academic_preparedness)
        + 0.20 * rng.random()
    )

    students.append(
        {
            "student_id": f"STU{i:06d}",
            "programme_code": programme_code,
            "programme": programme_name,
            "school": school,
            "year_of_study": year,
            "enrolment_status": "Active",
            "_baseline_engagement": round(baseline_engagement, 4),
            "_academic_preparedness": round(academic_preparedness, 4),
            "_support_need_signal": round(support_need_signal, 4),
        }
    )

students_df = pd.DataFrame(students)


# ============================================================
# 2. Courses
# ============================================================

courses_df = pd.DataFrame(
    COURSES,
    columns=[
        "course_id",
        "course_name",
        "credits",
        "department_code",
    ],
)

courses_df["semester"] = SEMESTER


# ============================================================
# 3. Enrolments
# ============================================================

enrolments = []

for student in students_df.itertuples(index=False):

    number_of_courses = int(rng.integers(4, 7))

    selected_courses = rng.choice(
        courses_df["course_id"].to_numpy(),
        size=number_of_courses,
        replace=False,
    )

    for course_id in selected_courses:

        enrolments.append(
            {
                "student_id": student.student_id,
                "course_id": course_id,
                "semester": SEMESTER,
                "status": "Enrolled",
            }
        )

enrolments_df = pd.DataFrame(enrolments)


# ============================================================
# 4. Attendance + LMS + Assignment activity
# ============================================================

attendance = []
lms_activity = []
assignment_submissions = []


for enrolment in enrolments_df.itertuples(index=False):

    student = students_df.loc[
        students_df["student_id"] == enrolment.student_id
    ].iloc[0]

    baseline = float(student["_baseline_engagement"])
    preparedness = float(student["_academic_preparedness"])

    for week in range(1, WEEKS + 1):

        # Create a mild trend.
        # Lower engagement students deteriorate slightly more often.
        deterioration = (
            (week - 1) * (1 - baseline) * 0.012
        )

        weekly_engagement = clip(
            baseline - deterioration + rng.normal(0, 0.045),
            0.05,
            0.99,
        )

        week_date = date_for_week(week)

        # ------------------------------
        # Attendance
        # ------------------------------

        attendance_probability = clip(
            0.55 + 0.42 * weekly_engagement,
            0.40,
            0.98,
        )

        attendance_status = (
            "PRESENT"
            if rng.random() < attendance_probability
            else "ABSENT"
        )

        attendance.append(
            {
                "student_id": enrolment.student_id,
                "course_id": enrolment.course_id,
                "attendance_date": week_date.date().isoformat(),
                "week_number": week,
                "status": attendance_status,
            }
        )

        # ------------------------------
        # LMS activity
        # ------------------------------

        expected_logins = (
            0.8 + 4.0 * weekly_engagement
        )

        login_count = int(
            max(
                0,
                rng.poisson(expected_logins),
            )
        )

        expected_minutes = (
            15 + 125 * weekly_engagement
        )

        minutes_active = int(
            max(
                0,
                rng.normal(
                    expected_minutes,
                    25,
                ),
            )
        )

        assignment_views = int(
            max(
                0,
                rng.poisson(
                    1 + 4 * weekly_engagement
                ),
            )
        )

        lms_activity.append(
            {
                "student_id": enrolment.student_id,
                "course_id": enrolment.course_id,
                "activity_date": week_date.date().isoformat(),
                "week_number": week,
                "login_count": login_count,
                "minutes_active": minutes_active,
                "assignment_views": assignment_views,
            }
        )

        # ------------------------------
        # Assignment submission
        # ------------------------------

        submission_probability = clip(
            0.30 + 0.65 * weekly_engagement,
            0.20,
            0.97,
        )

        submitted = (
            rng.random() < submission_probability
        )

        assignment_submissions.append(
            {
                "student_id": enrolment.student_id,
                "course_id": enrolment.course_id,
                "assignment_date": (
                    week_date + timedelta(days=5)
                ).date().isoformat(),
                "week_number": week,
                "submitted": int(submitted),
                "days_late": (
                    int(rng.integers(0, 4))
                    if submitted and rng.random() < 0.18
                    else 0
                ),
            }
        )


attendance_df = pd.DataFrame(attendance)

lms_df = pd.DataFrame(lms_activity)

assignment_df = pd.DataFrame(
    assignment_submissions
)


# ============================================================
# 5. Assessments
# ============================================================

assessments = []

for enrolment in enrolments_df.itertuples(index=False):

    student = students_df.loc[
        students_df["student_id"] == enrolment.student_id
    ].iloc[0]

    baseline = float(student["_baseline_engagement"])
    preparedness = float(student["_academic_preparedness"])

    for assessment_index, assessment_type in enumerate(
        ASSESSMENT_TYPES,
        start=1,
    ):

        # Performance is driven by preparedness and engagement.
        raw_score = (
            35
            + 35 * preparedness
            + 20 * baseline
            + rng.normal(0, 10)
            - assessment_index * (1 - baseline) * 5
        )

        score = clip(
            raw_score,
            20,
            100,
        )

        assessment_date = (
            START_DATE
            + timedelta(
                days=assessment_index * 21
            )
        )

        assessments.append(
            {
                "student_id": enrolment.student_id,
                "course_id": enrolment.course_id,
                "assessment_type": assessment_type,
                "assessment_date": assessment_date.date().isoformat(),
                "score": round(score, 1),
            }
        )


assessments_df = pd.DataFrame(assessments)


# ============================================================
# 6. Simulated intervention records
# ============================================================

interventions = []

for i in range(1, 181):

    student_id = rng.choice(
        students_df["student_id"].to_numpy()
    )

    risk_type = rng.choice(RISK_TYPES)

    trigger_date = (
        START_DATE
        + timedelta(
            days=int(rng.integers(7, WEEKS * 7))
        )
    )

    status = rng.choice(
        [
            "Pending",
            "In progress",
            "Completed",
        ],
        p=[
            0.18,
            0.32,
            0.50,
        ],
    )

    if status == "Pending":

        outcome = "Not yet assessed"

    else:

        outcome = rng.choice(
            INTERVENTION_OUTCOMES,
            p=[
                0.38,
                0.34,
                0.16,
                0.12,
            ],
        )

    interventions.append(
        {
            "intervention_id": f"INT{i:05d}",
            "student_id": student_id,
            "risk_type": risk_type,
            "trigger_date": trigger_date.date().isoformat(),
            "intervention_type": rng.choice(
                INTERVENTION_TYPES
            ),
            "advisor": f"Advisor {int(rng.integers(1, 16)):02d}",
            "status": status,
            "outcome": outcome,
        }
    )


interventions_df = pd.DataFrame(interventions)


# ============================================================
# 7. Simulation metadata / evaluation reference
# ============================================================

# This table is useful later for testing the analytics model.
# It must NOT be used as an input feature in the risk model.

simulation_truth_df = students_df[
    [
        "student_id",
        "_baseline_engagement",
        "_academic_preparedness",
        "_support_need_signal",
    ]
].copy()

simulation_truth_df["simulated_support_need"] = pd.cut(
    simulation_truth_df["_support_need_signal"],
    bins=[
        -np.inf,
        0.28,
        0.45,
        0.65,
        np.inf,
    ],
    labels=[
        "Low",
        "Moderate",
        "High",
        "Critical",
    ],
)

simulation_truth_df = simulation_truth_df[
    [
        "student_id",
        "simulated_support_need",
    ]
]


# ============================================================
# 8. Remove simulation-only fields from the public student table
# ============================================================

students_public_df = students_df.drop(
    columns=[
        "_baseline_engagement",
        "_academic_preparedness",
        "_support_need_signal",
    ]
)


# ============================================================
# 9. Introduce controlled data-quality issues
# ============================================================

# -----------------------------------
# Missing LMS activity
# -----------------------------------

missing_lms_count = min(
    30,
    len(lms_df),
)

if missing_lms_count > 0:

    missing_lms_indices = rng.choice(
        lms_df.index.to_numpy(),
        size=missing_lms_count,
        replace=False,
    )

    lms_df.loc[
        missing_lms_indices,
        "minutes_active",
    ] = np.nan


# -----------------------------------
# Duplicate attendance events
# -----------------------------------

duplicate_attendance_count = min(
    15,
    len(attendance_df),
)

if duplicate_attendance_count > 0:

    duplicate_attendance_rows = (
        attendance_df.sample(
            duplicate_attendance_count,
            random_state=RANDOM_SEED,
        )
    )

    attendance_df = pd.concat(
        [
            attendance_df,
            duplicate_attendance_rows,
        ],
        ignore_index=True,
    )


# -----------------------------------
# Missing assignment submission value
# -----------------------------------

missing_assignment_count = min(
    10,
    len(assignment_df),
)

if missing_assignment_count > 0:

    missing_assignment_indices = rng.choice(
        assignment_df.index.to_numpy(),
        size=missing_assignment_count,
        replace=False,
    )

    assignment_df.loc[
        missing_assignment_indices,
        "submitted",
    ] = np.nan


# ============================================================
# 10. Save all datasets
# ============================================================

datasets = {
    "students.csv": students_public_df,
    "courses.csv": courses_df,
    "enrolments.csv": enrolments_df,
    "attendance.csv": attendance_df,
    "lms_activity.csv": lms_df,
    "assignment_submissions.csv": assignment_df,
    "assessments.csv": assessments_df,
    "interventions.csv": interventions_df,
    "simulation_truth.csv": simulation_truth_df,
}


print("\nGenerating synthetic university dataset...\n")


for filename, dataframe in datasets.items():

    output_path = OUTPUT_DIR / filename

    dataframe.to_csv(
        output_path,
        index=False,
    )

    print(
        f"✓ {filename:<30} "
        f"{len(dataframe):>8,} rows"
    )


# ============================================================
# 11. Summary
# ============================================================

print("\n" + "=" * 60)
print("SYNTHETIC DATASET GENERATION COMPLETE")
print("=" * 60)

print(
    f"Students:                 {len(students_public_df):,}"
)

print(
    f"Courses:                  {len(courses_df):,}"
)

print(
    f"Enrolments:               {len(enrolments_df):,}"
)

print(
    f"Attendance events:        {len(attendance_df):,}"
)

print(
    f"LMS activity records:     {len(lms_df):,}"
)

print(
    f"Assignment records:       {len(assignment_df):,}"
)

print(
    f"Assessment records:       {len(assessments_df):,}"
)

print(
    f"Intervention records:     {len(interventions_df):,}"
)

print(
    f"Output directory:         {OUTPUT_DIR.resolve()}"
)

print("=" * 60)

print(
    "\nImportant: simulation_truth.csv is for model evaluation only "
    "and must never be used as a model input feature."
)