"""
Load synthetic survey analytics into SQLite.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "survey_reports"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


TABLES = {
    "survey_summary":
        "survey_summary.csv",

    "survey_respondent_summary":
        "survey_respondent_summary.csv",

    "survey_theme_summary":
        "survey_theme_summary.csv",

    "survey_trend":
        "survey_trend.csv",
}


if not DATABASE_PATH.exists():

    raise FileNotFoundError(
        f"Database not found: {DATABASE_PATH}"
    )


connection = sqlite3.connect(
    DATABASE_PATH
)


try:

    print()
    print("=" * 72)
    print(
        "STUDENT SUCCESS ANALYTICS — LOAD SURVEY DATA"
    )
    print("=" * 72)

    for table_name, filename in TABLES.items():

        path = DATA_DIR / filename

        if not path.exists():

            raise FileNotFoundError(
                f"Survey report not found: {path}"
            )

        df = pd.read_csv(
            path
        )

        df.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )

        print(
            f"✓ {table_name:<36}"
            f"{len(df):>8,} rows"
        )

    connection.commit()

finally:

    connection.close()


print()
print("=" * 72)
print(
    "SURVEY DATA LOADED INTO SQLITE"
)
print("=" * 72)
