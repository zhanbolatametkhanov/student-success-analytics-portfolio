
"""
Load synthetic outcome-analysis reports into SQLite.
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
    / "outcome_reports"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


TABLES = {
    "outcome_summary_metrics":
        "outcome_summary_metrics.csv",

    "intervention_type_summary":
        "intervention_type_summary.csv",

    "risk_type_outcome_summary":
        "risk_type_outcome_summary.csv",

    "outcome_distribution":
        "outcome_distribution.csv",

    "intervention_status_funnel":
        "intervention_status_funnel.csv",

    "advisor_workload_summary":
        "advisor_workload_summary.csv",

    "illustrative_cost_assumptions":
        "illustrative_cost_assumptions.csv",
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
        "STUDENT SUCCESS ANALYTICS — LOAD OUTCOME DATA"
    )
    print("=" * 72)

    for table_name, filename in TABLES.items():

        path = (
            DATA_DIR
            / filename
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Outcome report not found: {path}"
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
        idx_outcome_type
        ON intervention_type_summary (
            intervention_type
        )
        """
    )


    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_outcome_risk_type
        ON risk_type_outcome_summary (
            risk_type
        )
        """
    )


    connection.commit()

finally:

    connection.close()


print()
print("=" * 72)
print(
    "OUTCOME DATA LOADED INTO SQLITE"
)
print("=" * 72)
