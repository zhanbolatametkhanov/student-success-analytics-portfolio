"""
Load student-profile analytical datasets into SQLite.

All records are synthetic.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "profile_reports"
)


DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


TABLES = {
    "weekly_student_profile":
        "weekly_student_profile.csv",

    "student_assessment_trajectory":
        "student_assessment_trajectory.csv",
}


print()
print("=" * 72)
print(
    "STUDENT SUCCESS ANALYTICS — LOAD PROFILE DATA"
)
print("=" * 72)


if not DATABASE_PATH.exists():

    raise FileNotFoundError(
        f"Database not found: {DATABASE_PATH}"
    )


connection = sqlite3.connect(
    DATABASE_PATH
)


try:

    for table_name, filename in TABLES.items():

        path = DATA_DIR / filename

        if not path.exists():

            raise FileNotFoundError(
                f"Profile report not found: {path}"
            )

        dataframe = pd.read_csv(
            path
        )

        dataframe.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )

        print(
            f"✓ {table_name:<36}"
            f"{len(dataframe):>8,} rows"
        )


    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_weekly_profile_student_week
        ON weekly_student_profile (
            student_id,
            week_number
        )
        """
    )


    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_assessment_trajectory_student
        ON student_assessment_trajectory (
            student_id
        )
        """
    )


    connection.commit()


finally:

    connection.close()


print()
print("=" * 72)
print(
    "PROFILE DATA LOADED INTO SQLITE"
)
print("=" * 72)
