"""
Student Success Analytics
Reproducible Demo Environment Builder

Purpose
-------
Build the complete synthetic analytical environment from source
data and Python scripts.

Execution order:

1. Generate source data when necessary
2. Validate data quality
3. Calculate risk indicators
4. Evaluate the risk model
5. Analyse thresholds
6. Generate integration telemetry
7. Build SQLite
8. Load integration telemetry into SQLite

This script is intended to make the public portfolio reproducible
from a clean checkout of the GitHub repository.

IMPORTANT
---------
All data is synthetic.
No real student or institutional information is used.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)


PYTHON_DIR = PROJECT_ROOT / "python"


DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


STUDENT_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "students.csv"
)


# ============================================================
# Helpers
# ============================================================

def run_script(script_name: str) -> None:
    """Execute a Python project script."""

    script_path = PYTHON_DIR / script_name

    if not script_path.exists():

        raise FileNotFoundError(
            f"Required script not found: {script_path}"
        )

    print(
        f"\n{'=' * 72}"
    )

    print(
        f"RUNNING: {script_name}"
    )

    print(
        f"{'=' * 72}\n"
    )

    subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )


# ============================================================
# Main
# ============================================================

print("\n")
print("=" * 72)
print("STUDENT SUCCESS ANALYTICS")
print("REPRODUCIBLE DEMO ENVIRONMENT BUILDER")
print("=" * 72)


# ------------------------------------------------------------
# 1. Generate source data if necessary
# ------------------------------------------------------------

if not STUDENT_DATA_PATH.exists():

    run_script(
        "data_generation.py"
    )

else:

    print(
        "\n✓ Synthetic source data already exists."
    )


# ------------------------------------------------------------
# 2. Data quality
# ------------------------------------------------------------

run_script(
    "data_quality.py"
)


# ------------------------------------------------------------
# 3. Risk analysis
# ------------------------------------------------------------

run_script(
    "risk_analysis.py"
)


# ------------------------------------------------------------
# 4. Model evaluation
# ------------------------------------------------------------

run_script(
    "model_evaluation.py"
)


# ------------------------------------------------------------
# 5. Threshold analysis
# ------------------------------------------------------------

run_script(
    "threshold_analysis.py"
)

run_script(
    "outcome_analysis.py"
)


# ------------------------------------------------------------
# 6. Integration telemetry
# ------------------------------------------------------------

run_script(
    "integration_monitor.py"
)


# ------------------------------------------------------------
# 7. Build SQLite
# ------------------------------------------------------------

run_script(
    "build_database.py"
)


# ------------------------------------------------------------
# 8. Load integration telemetry
# ------------------------------------------------------------

run_script(
    "load_integration_data.py"
)

run_script(
    "load_outcome_data.py"
)


# ============================================================
# Verification
# ============================================================

if not DATABASE_PATH.exists():

    raise RuntimeError(
        "Environment build completed but SQLite database "
        "was not created."
    )


print("\n")
print("=" * 72)
print("DEMO ENVIRONMENT READY")
print("=" * 72)

print(
    f"\nDatabase:"
)

print(
    DATABASE_PATH
)

print(
    "\nThe environment can now be consumed by the Streamlit application."
)

print("=" * 72)