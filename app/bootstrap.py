"""
Streamlit startup bootstrap.

Ensures the synthetic SQLite environment exists before
the application attempts to query it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)


DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "database"
    / "student_success.db"
)


BUILD_SCRIPT = (
    PROJECT_ROOT
    / "python"
    / "build_demo_environment.py"
)


def ensure_demo_environment() -> None:
    """
    Build the synthetic analytical environment if the
    generated SQLite database is not available.
    """

    if DATABASE_PATH.exists():
        return

    if not BUILD_SCRIPT.exists():

        raise FileNotFoundError(
            f"Environment builder not found: {BUILD_SCRIPT}"
        )

    subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )