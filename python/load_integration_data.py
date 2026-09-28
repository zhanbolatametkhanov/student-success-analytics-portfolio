"""
Load synthetic integration-monitoring data into SQLite.

All data is synthetic.
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
    / "integration"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


TABLES = {
    "integration_health":
        DATA_DIR / "integration_health.csv",

    "integration_events":
        DATA_DIR / "integration_events.csv",
}


print("\n")
print("=" * 72)
print(
    "STUDENT SUCCESS ANALYTICS — LOAD INTEGRATION DATA"
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

    for table_name, path in TABLES.items():

        if not path.exists():

            raise FileNotFoundError(
                f"File not found: {path}"
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
            f"✓ {table_name:<25}"
            f"{len(dataframe):>8,} rows"
        )


    # --------------------------------------------------------
    # Indexes
    # --------------------------------------------------------

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_integration_health_id
        ON integration_health (
            integration_id
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_integration_health_status
        ON integration_health (
            status
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_integration_events_id
        ON integration_events (
            integration_id
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_integration_events_status
        ON integration_events (
            status
        )
        """
    )

    connection.commit()

finally:

    connection.close()


print("\n")
print("=" * 72)
print(
    "INTEGRATION DATA LOADED INTO SQLITE"
)
print("=" * 72)